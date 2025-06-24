import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/contexts/AuthContext'
import { 
  Container, 
  FolderOpen, 
  Play, 
  Github, 
  Activity,
  TrendingUp,
  Clock,
  Users
} from 'lucide-react'

export default function Dashboard() {
  const { apiCall } = useAuth()
  const [stats, setStats] = useState({
    projects: 0,
    containers: 0,
    executions: 0,
    activeContainers: 0
  })
  const [recentProjects, setRecentProjects] = useState([])
  const [recentExecutions, setRecentExecutions] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      
      // Fetch projects
      const projectsResponse = await apiCall('/projects')
      if (projectsResponse.ok) {
        const projects = await projectsResponse.json()
        setStats(prev => ({ ...prev, projects: projects.length }))
        setRecentProjects(projects.slice(0, 5))
      }

      // Fetch containers
      const containersResponse = await apiCall('/containers')
      if (containersResponse.ok) {
        const containersData = await containersResponse.json()
        const containers = containersData.containers || []
        const activeContainers = containers.filter(c => c.status === 'running').length
        setStats(prev => ({ 
          ...prev, 
          containers: containers.length,
          activeContainers 
        }))
      }

      // Fetch system info
      const systemResponse = await apiCall('/containers/system-info')
      if (systemResponse.ok) {
        const systemData = await systemResponse.json()
        setStats(prev => ({ 
          ...prev, 
          executions: systemData.containers || 0
        }))
      }

    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const StatCard = ({ title, value, description, icon: Icon, trend }) => (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{loading ? '...' : value}</div>
        <p className="text-xs text-muted-foreground">
          {description}
        </p>
        {trend && (
          <div className="flex items-center pt-1">
            <TrendingUp className="h-3 w-3 text-green-500 mr-1" />
            <span className="text-xs text-green-500">{trend}</span>
          </div>
        )}
      </CardContent>
    </Card>
  )

  const getLanguageBadgeColor = (language) => {
    const colors = {
      python: 'bg-blue-100 text-blue-800',
      javascript: 'bg-yellow-100 text-yellow-800',
      nodejs: 'bg-green-100 text-green-800',
      java: 'bg-red-100 text-red-800',
      go: 'bg-cyan-100 text-cyan-800',
      rust: 'bg-orange-100 text-orange-800',
      php: 'bg-purple-100 text-purple-800',
      cpp: 'bg-gray-100 text-gray-800'
    }
    return colors[language] || 'bg-gray-100 text-gray-800'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        <p className="text-muted-foreground">
          Overview of your compiler server activity
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Projects"
          value={stats.projects}
          description="Active development projects"
          icon={FolderOpen}
          trend="+2 from last week"
        />
        <StatCard
          title="Containers"
          value={stats.containers}
          description="Docker containers created"
          icon={Container}
          trend="+5 from last week"
        />
        <StatCard
          title="Active Containers"
          value={stats.activeContainers}
          description="Currently running"
          icon={Activity}
          trend="Real-time"
        />
        <StatCard
          title="Code Executions"
          value={stats.executions}
          description="Total executions today"
          icon={Play}
          trend="+12% from yesterday"
        />
      </div>

      {/* Recent Activity */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Recent Projects */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <FolderOpen className="mr-2 h-5 w-5" />
              Recent Projects
            </CardTitle>
            <CardDescription>
              Your latest development projects
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-3">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="animate-pulse">
                    <div className="h-4 bg-muted rounded w-3/4 mb-2"></div>
                    <div className="h-3 bg-muted rounded w-1/2"></div>
                  </div>
                ))}
              </div>
            ) : recentProjects.length > 0 ? (
              <div className="space-y-4">
                {recentProjects.map((project) => (
                  <div key={project.id} className="flex items-center justify-between">
                    <div className="space-y-1">
                      <p className="text-sm font-medium leading-none">
                        {project.name}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {project.description || 'No description'}
                      </p>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge 
                        variant="secondary" 
                        className={getLanguageBadgeColor(project.language)}
                      >
                        {project.language}
                      </Badge>
                      <Badge 
                        variant={project.container_status === 'running' ? 'default' : 'secondary'}
                      >
                        {project.container_status || 'stopped'}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-6">
                <FolderOpen className="mx-auto h-12 w-12 text-muted-foreground" />
                <h3 className="mt-2 text-sm font-semibold">No projects</h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  Get started by creating a new project.
                </p>
                <Button className="mt-4" size="sm">
                  Create Project
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* System Status */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Activity className="mr-2 h-5 w-5" />
              System Status
            </CardTitle>
            <CardDescription>
              Current system health and metrics
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm">API Server</span>
                </div>
                <Badge variant="default">Online</Badge>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm">Docker Engine</span>
                </div>
                <Badge variant="default">Running</Badge>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className="h-2 w-2 bg-blue-500 rounded-full"></div>
                  <span className="text-sm">Database</span>
                </div>
                <Badge variant="default">Connected</Badge>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className="h-2 w-2 bg-yellow-500 rounded-full"></div>
                  <span className="text-sm">GitHub Integration</span>
                </div>
                <Badge variant="secondary">Available</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>
            Common tasks and shortcuts
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <Button className="h-20 flex-col space-y-2">
              <FolderOpen className="h-6 w-6" />
              <span>New Project</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col space-y-2">
              <Github className="h-6 w-6" />
              <span>Clone Repository</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col space-y-2">
              <Container className="h-6 w-6" />
              <span>Manage Containers</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

