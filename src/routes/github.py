"""
GitHub Integration API Routes
Handles GitHub repository operations
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from github import Github
from src.models.project import Project
from src.models.container_manager import ContainerManager
import os
import tempfile
import shutil
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
github_bp = Blueprint('github', __name__)

# Initialize container manager
container_manager = ContainerManager()

def get_github_client(token=None):
    """Get GitHub client with optional token"""
    if token:
        return Github(token)
    else:
        # Use environment variable or return unauthenticated client
        github_token = os.getenv('GITHUB_TOKEN')
        if github_token:
            return Github(github_token)
        else:
            return Github()  # Unauthenticated (limited API calls)

@github_bp.route('/github/clone', methods=['POST'])
@jwt_required(optional=True)
def clone_repository():
    """Clone a GitHub repository"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'repository_url' not in data:
            return jsonify({'error': 'repository_url is required'}), 400
        
        repository_url = data['repository_url']
        branch = data.get('branch', 'main')
        project_id = data.get('project_id')
        github_token = data.get('github_token')
        
        # Parse repository URL to get owner and repo name
        if 'github.com/' in repository_url:
            # Extract owner/repo from URL
            parts = repository_url.replace('https://github.com/', '').replace('http://github.com/', '').replace('.git', '').split('/')
            if len(parts) >= 2:
                owner = parts[0]
                repo_name = parts[1]
            else:
                return jsonify({'error': 'Invalid GitHub repository URL'}), 400
        else:
            return jsonify({'error': 'Invalid GitHub repository URL'}), 400
        
        # Get GitHub client
        github_client = get_github_client(github_token)
        
        try:
            # Get repository information
            repo = github_client.get_repo(f"{owner}/{repo_name}")
            
            # Get repository contents
            try:
                contents = repo.get_contents("", ref=branch)
            except:
                # Try with default branch if specified branch doesn't exist
                contents = repo.get_contents("")
                branch = repo.default_branch
            
            # Create project if not provided
            if not project_id:
                # Detect language from repository
                languages = repo.get_languages()
                primary_language = max(languages.keys(), key=lambda k: languages[k]) if languages else 'python'
                
                # Map GitHub language names to our supported languages
                language_mapping = {
                    'Python': 'python',
                    'JavaScript': 'nodejs',
                    'TypeScript': 'nodejs',
                    'Java': 'java',
                    'Go': 'go',
                    'Rust': 'rust',
                    'PHP': 'php',
                    'C++': 'cpp',
                    'C': 'cpp'
                }
                
                detected_language = language_mapping.get(primary_language, 'python')
                
                # Create new project
                project = Project(
                    name=repo_name,
                    language=detected_language,
                    description=repo.description,
                    github_url=repository_url,
                    user_id=get_jwt_identity() if get_jwt_identity() else None
                )
                project.github_branch = branch
                project.save()
                project_id = project.id
                
                # Create container for the project
                container_id, success = container_manager.create_container(
                    language=detected_language,
                    project_id=project_id
                )
                
                if success and container_id:
                    project.set_container(container_id, 'created')
                    project.save()
            else:
                project = Project.get_by_id(project_id)
                if not project:
                    return jsonify({'error': 'Project not found'}), 404
            
            # Download repository files
            files_structure = {}
            
            def download_contents(contents, path=""):
                for content in contents:
                    if content.type == "dir":
                        # Recursively get directory contents
                        dir_contents = repo.get_contents(content.path, ref=branch)
                        download_contents(dir_contents, content.path)
                    else:
                        # Download file content
                        try:
                            file_content = content.decoded_content.decode('utf-8')
                            files_structure[content.path] = file_content
                        except:
                            # Skip binary files or files that can't be decoded
                            logger.warning(f"Skipped binary file: {content.path}")
            
            download_contents(contents)
            
            # Update project files
            project.update_files(files_structure)
            project.github_url = repository_url
            project.github_branch = branch
            project.save()
            
            # Copy files to container workspace if container exists
            if project.container_id:
                try:
                    # Start container
                    container_manager.start_container(project.container_id)
                    
                    # Create files in container
                    for file_path, file_content in files_structure.items():
                        # Create directory structure
                        dir_path = os.path.dirname(file_path)
                        if dir_path:
                            container_manager.execute_command(
                                project.container_id,
                                f"mkdir -p /workspace/{dir_path}"
                            )
                        
                        # Write file content (escape quotes and special characters)
                        escaped_content = file_content.replace('"', '\\"').replace('`', '\\`').replace('$', '\\$')
                        container_manager.execute_command(
                            project.container_id,
                            f'echo "{escaped_content}" > /workspace/{file_path}'
                        )
                except Exception as e:
                    logger.warning(f"Failed to copy files to container: {e}")
            
            logger.info(f"Cloned repository {repository_url} to project {project_id}")
            return jsonify({
                'message': 'Repository cloned successfully',
                'project_id': project_id,
                'repository_url': repository_url,
                'branch': branch,
                'files_count': len(files_structure),
                'project': project.to_dict()
            }), 200
            
        except Exception as e:
            logger.error(f"Error accessing repository {repository_url}: {e}")
            return jsonify({'error': f'Failed to access repository: {str(e)}'}), 400
        
    except Exception as e:
        logger.error(f"Error cloning repository: {e}")
        return jsonify({'error': str(e)}), 500

@github_bp.route('/github/push', methods=['POST'])
@jwt_required(optional=True)
def push_to_repository():
    """Push changes to GitHub repository"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'project_id' not in data or 'github_token' not in data:
            return jsonify({'error': 'project_id and github_token are required'}), 400
        
        project_id = data['project_id']
        github_token = data['github_token']
        commit_message = data.get('commit_message', 'Update from Compiler Server')
        branch = data.get('branch')
        
        # Get project
        project = Project.get_by_id(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        if not project.github_url:
            return jsonify({'error': 'Project is not linked to a GitHub repository'}), 400
        
        # Parse repository URL
        repository_url = project.github_url
        if 'github.com/' in repository_url:
            parts = repository_url.replace('https://github.com/', '').replace('http://github.com/', '').replace('.git', '').split('/')
            if len(parts) >= 2:
                owner = parts[0]
                repo_name = parts[1]
            else:
                return jsonify({'error': 'Invalid GitHub repository URL'}), 400
        else:
            return jsonify({'error': 'Invalid GitHub repository URL'}), 400
        
        # Use project branch if not specified
        if not branch:
            branch = project.github_branch or 'main'
        
        # Get GitHub client with token
        github_client = get_github_client(github_token)
        
        try:
            # Get repository
            repo = github_client.get_repo(f"{owner}/{repo_name}")
            
            # Get project files
            files = project.get_files()
            
            if not files:
                return jsonify({'error': 'No files to push'}), 400
            
            # Get current branch reference
            try:
                ref = repo.get_git_ref(f"heads/{branch}")
                base_sha = ref.object.sha
            except:
                # Branch doesn't exist, create it from default branch
                default_ref = repo.get_git_ref(f"heads/{repo.default_branch}")
                base_sha = default_ref.object.sha
                repo.create_git_ref(f"refs/heads/{branch}", base_sha)
            
            # Get current tree
            base_tree = repo.get_git_tree(base_sha, recursive=True)
            
            # Create new tree with updated files
            tree_elements = []
            
            for file_path, file_content in files.items():
                # Create blob for file content
                blob = repo.create_git_blob(file_content, "utf-8")
                
                # Add to tree elements
                tree_elements.append({
                    "path": file_path,
                    "mode": "100644",  # File mode
                    "type": "blob",
                    "sha": blob.sha
                })
            
            # Create new tree
            new_tree = repo.create_git_tree(tree_elements, base_tree)
            
            # Create commit
            commit = repo.create_git_commit(
                message=commit_message,
                tree=new_tree,
                parents=[repo.get_git_commit(base_sha)]
            )
            
            # Update branch reference
            ref = repo.get_git_ref(f"heads/{branch}")
            ref.edit(commit.sha)
            
            logger.info(f"Pushed changes to repository {repository_url} branch {branch}")
            return jsonify({
                'message': 'Changes pushed successfully',
                'commit_sha': commit.sha,
                'commit_url': f"https://github.com/{owner}/{repo_name}/commit/{commit.sha}",
                'branch': branch,
                'files_count': len(files)
            }), 200
            
        except Exception as e:
            logger.error(f"Error pushing to repository {repository_url}: {e}")
            return jsonify({'error': f'Failed to push to repository: {str(e)}'}), 400
        
    except Exception as e:
        logger.error(f"Error pushing to repository: {e}")
        return jsonify({'error': str(e)}), 500

@github_bp.route('/github/repositories', methods=['GET'])
@jwt_required(optional=True)
def list_user_repositories():
    """List user's GitHub repositories"""
    try:
        github_token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not github_token:
            return jsonify({'error': 'GitHub token is required'}), 400
        
        # Get GitHub client
        github_client = get_github_client(github_token)
        
        try:
            # Get authenticated user
            user = github_client.get_user()
            
            # Get user repositories
            repos = user.get_repos(sort='updated', direction='desc')
            
            repositories = []
            for repo in repos[:50]:  # Limit to 50 repositories
                repositories.append({
                    'name': repo.name,
                    'full_name': repo.full_name,
                    'description': repo.description,
                    'html_url': repo.html_url,
                    'clone_url': repo.clone_url,
                    'language': repo.language,
                    'default_branch': repo.default_branch,
                    'updated_at': repo.updated_at.isoformat() if repo.updated_at else None,
                    'private': repo.private
                })
            
            return jsonify({
                'repositories': repositories,
                'count': len(repositories)
            }), 200
            
        except Exception as e:
            logger.error(f"Error accessing GitHub user repositories: {e}")
            return jsonify({'error': f'Failed to access repositories: {str(e)}'}), 400
        
    except Exception as e:
        logger.error(f"Error listing repositories: {e}")
        return jsonify({'error': str(e)}), 500

@github_bp.route('/github/repository/<owner>/<repo>/info', methods=['GET'])
@jwt_required(optional=True)
def get_repository_info(owner, repo):
    """Get information about a specific repository"""
    try:
        github_token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        # Get GitHub client
        github_client = get_github_client(github_token)
        
        try:
            # Get repository
            repository = github_client.get_repo(f"{owner}/{repo}")
            
            # Get languages
            languages = repository.get_languages()
            
            # Get branches
            branches = [branch.name for branch in repository.get_branches()]
            
            repo_info = {
                'name': repository.name,
                'full_name': repository.full_name,
                'description': repository.description,
                'html_url': repository.html_url,
                'clone_url': repository.clone_url,
                'language': repository.language,
                'languages': languages,
                'default_branch': repository.default_branch,
                'branches': branches,
                'created_at': repository.created_at.isoformat() if repository.created_at else None,
                'updated_at': repository.updated_at.isoformat() if repository.updated_at else None,
                'size': repository.size,
                'stargazers_count': repository.stargazers_count,
                'forks_count': repository.forks_count,
                'private': repository.private
            }
            
            return jsonify(repo_info), 200
            
        except Exception as e:
            logger.error(f"Error accessing repository {owner}/{repo}: {e}")
            return jsonify({'error': f'Failed to access repository: {str(e)}'}), 400
        
    except Exception as e:
        logger.error(f"Error getting repository info: {e}")
        return jsonify({'error': str(e)}), 500

