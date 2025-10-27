import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({
      error,
      errorInfo,
    });
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-screen flex items-center justify-center p-4">
          <div className="max-w-2xl w-full">
            <Alert variant="destructive" className="mb-4">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                <div className="space-y-4">
                  <div>
                    <h3 className="font-semibold mb-2">Something went wrong</h3>
                    <p className="text-sm">
                      {this.state.error?.message || 'An unexpected error occurred'}
                    </p>
                  </div>
                  
                  {process.env.NODE_ENV === 'development' && this.state.errorInfo && (
                    <div className="text-xs bg-muted p-3 rounded overflow-auto max-h-64">
                      <pre className="whitespace-pre-wrap">
                        {this.state.errorInfo.componentStack}
                      </pre>
                    </div>
                  )}

                  <div className="flex gap-2">
                    <Button onClick={this.handleReset} size="sm">
                      Try Again
                    </Button>
                    <Button 
                      onClick={() => window.location.href = '/'} 
                      variant="outline" 
                      size="sm"
                    >
                      Go to Dashboard
                    </Button>
                  </div>
                </div>
              </AlertDescription>
            </Alert>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
