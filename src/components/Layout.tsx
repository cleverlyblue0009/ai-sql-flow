import { useState } from "react";
import { Outlet, useLocation, NavLink } from "react-router-dom";
import { useAuthSync } from "@/hooks/useAuthSync";
import { 
  BarChart3, 
  Database, 
  GitBranch, 
  Settings, 
  Menu, 
  X,
  Shield,
  Activity,
  LogOut,
  User
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuLabel, 
  DropdownMenuSeparator, 
  DropdownMenuTrigger 
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@/contexts/AuthContext";
import { cn } from "@/lib/utils";

const navigation = [
  { name: 'Dashboard', href: '/', icon: BarChart3 },
  { name: 'Data Quality', href: '/data-quality', icon: Shield },
  { name: 'SQL Migration', href: '/sql-migration', icon: GitBranch },
  { name: 'Monitoring', href: '/monitoring', icon: Activity },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();
  
  // Sync Firebase auth with backend
  useAuthSync();

  return (
    <div className="min-h-screen bg-background">
      {/* Mobile sidebar */}
      <div className={cn(
        "fixed inset-0 flex z-40 md:hidden",
        sidebarOpen ? "block" : "hidden"
      )}>
        <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={() => setSidebarOpen(false)} />
        <div className="relative flex-1 flex flex-col max-w-xs w-full bg-sidebar border-r border-border">
          <div className="absolute top-0 right-0 -mr-12 pt-2">
            <Button
              variant="ghost"
              size="icon"
              className="text-white"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="h-6 w-6" />
            </Button>
          </div>
          <SidebarContent />
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0">
        <div className="flex-1 flex flex-col min-h-0 bg-sidebar border-r border-border">
          <SidebarContent />
        </div>
      </div>

      {/* Main content */}
      <div className="md:pl-64 flex flex-col flex-1">
        <div className="sticky top-0 z-10 md:hidden pl-1 pt-1 sm:pl-3 sm:pt-3 bg-background border-b border-border">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-6 w-6" />
          </Button>
        </div>
        <main className="flex-1 p-4 md:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

function SidebarContent() {
  const location = useLocation();
  const { currentUser, logout } = useAuth();

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  return (
    <div className="flex-1 flex flex-col pt-5 pb-4 overflow-y-auto">
      <div className="flex items-center flex-shrink-0 px-4">
        <div className="flex items-center space-x-3">
          <Database className="h-8 w-8 text-primary" />
          <div>
            <h1 className="text-xl font-bold text-sidebar-foreground">DataFlow AI</h1>
            <p className="text-sm text-sidebar-foreground/70">Enterprise Platform</p>
          </div>
        </div>
      </div>
      
      <nav className="mt-8 flex-1 px-2 space-y-1">
        {navigation.map((item) => {
          const isActive = location.pathname === item.href;
          return (
            <NavLink
              key={item.name}
              to={item.href}
              className={cn(
                "group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors duration-200",
                isActive
                  ? "bg-sidebar-accent text-sidebar-accent-foreground"
                  : "text-sidebar-foreground hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground"
              )}
            >
              <item.icon className="mr-3 h-5 w-5 flex-shrink-0" />
              {item.name}
            </NavLink>
          );
        })}
      </nav>

      {/* User section at bottom */}
      <div className="flex-shrink-0 px-2">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="w-full justify-start px-2 py-2 h-auto">
              <div className="flex items-center space-x-3">
                <Avatar className="h-8 w-8">
                  <AvatarImage src={currentUser?.photoURL || undefined} />
                  <AvatarFallback>
                    {currentUser?.displayName?.charAt(0) || currentUser?.email?.charAt(0) || 'U'}
                  </AvatarFallback>
                </Avatar>
                <div className="flex flex-col items-start text-left">
                  <p className="text-sm font-medium text-sidebar-foreground">
                    {currentUser?.displayName || 'User'}
                  </p>
                  <p className="text-xs text-sidebar-foreground/70">
                    {currentUser?.email}
                  </p>
                </div>
              </div>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel>My Account</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem>
              <User className="mr-2 h-4 w-4" />
              Profile
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Settings className="mr-2 h-4 w-4" />
              Settings
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleLogout}>
              <LogOut className="mr-2 h-4 w-4" />
              Log out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}