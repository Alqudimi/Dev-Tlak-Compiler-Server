import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  LayoutDashboard, 
  FolderOpen, 
  Container, 
  Play, 
  Github, 
  Terminal,
  ChevronLeft,
  ChevronRight,
  Code2
} from 'lucide-react'

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Projects', href: '/projects', icon: FolderOpen },
  { name: 'Containers', href: '/containers', icon: Container },
  { name: 'Execution', href: '/execution', icon: Play },
  { name: 'GitHub', href: '/github', icon: Github },
  { name: 'Terminal', href: '/terminal', icon: Terminal },
]

export default function Sidebar({ isOpen }) {
  const location = useLocation()
  const [collapsed, setCollapsed] = useState(false)

  if (!isOpen) return null

  return (
    <div className={cn(
      "bg-sidebar border-r border-sidebar-border transition-all duration-300",
      collapsed ? "w-16" : "w-64"
    )}>
      <div className="flex h-full flex-col">
        {/* Header */}
        <div className="flex h-16 items-center justify-between px-4 border-b border-sidebar-border">
          {!collapsed && (
            <div className="flex items-center space-x-2">
              <Code2 className="h-8 w-8 text-sidebar-primary" />
              <span className="text-lg font-semibold text-sidebar-foreground">
                Compiler Server
              </span>
            </div>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setCollapsed(!collapsed)}
            className="text-sidebar-foreground hover:bg-sidebar-accent"
          >
            {collapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <ChevronLeft className="h-4 w-4" />
            )}
          </Button>
        </div>

        {/* Navigation */}
        <ScrollArea className="flex-1 px-3 py-4">
          <nav className="space-y-2">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={cn(
                    "flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                    "hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                    isActive
                      ? "bg-sidebar-primary text-sidebar-primary-foreground"
                      : "text-sidebar-foreground"
                  )}
                >
                  <item.icon className={cn("h-5 w-5", collapsed ? "mx-auto" : "mr-3")} />
                  {!collapsed && <span>{item.name}</span>}
                </Link>
              )
            })}
          </nav>
        </ScrollArea>

        {/* Footer */}
        {!collapsed && (
          <div className="border-t border-sidebar-border p-4">
            <div className="text-xs text-sidebar-foreground/60">
              Compiler Server v1.0
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

