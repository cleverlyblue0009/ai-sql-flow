import { useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

/**
 * Hook to sync Firebase authentication with backend
 */
export function useAuthSync() {
  const { currentUser } = useAuth();
  const { toast } = useToast();

  useEffect(() => {
    const syncAuthWithBackend = async () => {
      if (!currentUser) return;

      try {
        // Get Firebase ID token
        const token = await currentUser.getIdToken();
        
        // Sync with backend
        await apiClient.authenticateWithFirebase(token);
        
        console.log('Authentication synced with backend');
      } catch (error) {
        console.error('Failed to sync auth with backend:', error);
        
        // Show error toast but don't block the user
        toast({
          title: "Authentication Warning",
          description: "Some features may be limited. Please refresh the page if you experience issues.",
          variant: "destructive"
        });
      }
    };

    syncAuthWithBackend();
  }, [currentUser, toast]);

  return { currentUser };
}