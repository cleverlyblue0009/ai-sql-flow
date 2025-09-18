import React, { useState, useEffect } from 'react';
import { testFirebaseConnectivity, getFirebaseStatus } from '@/lib/firebase-test';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export const FirebaseDebug: React.FC = () => {
  const [status, setStatus] = useState<any>(null);
  const [connectivity, setConnectivity] = useState<boolean | null>(null);
  const [testing, setTesting] = useState(false);

  useEffect(() => {
    setStatus(getFirebaseStatus());
  }, []);

  const handleTestConnectivity = async () => {
    setTesting(true);
    const result = await testFirebaseConnectivity();
    setConnectivity(result);
    setTesting(false);
  };

  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <CardTitle>Firebase Debug Information</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <h3 className="font-semibold mb-2">Configuration Status:</h3>
          <pre className="bg-gray-100 p-2 rounded text-xs overflow-auto">
            {JSON.stringify(status, null, 2)}
          </pre>
        </div>
        
        <div>
          <h3 className="font-semibold mb-2">Environment Variables:</h3>
          <pre className="bg-gray-100 p-2 rounded text-xs overflow-auto">
            {JSON.stringify({
              VITE_FIREBASE_API_KEY: import.meta.env.VITE_FIREBASE_API_KEY ? 'Set' : 'Missing',
              VITE_FIREBASE_AUTH_DOMAIN: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || 'Missing',
              VITE_FIREBASE_PROJECT_ID: import.meta.env.VITE_FIREBASE_PROJECT_ID || 'Missing',
              VITE_FIREBASE_STORAGE_BUCKET: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || 'Missing',
              VITE_FIREBASE_MESSAGING_SENDER_ID: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID ? 'Set' : 'Missing',
              VITE_FIREBASE_APP_ID: import.meta.env.VITE_FIREBASE_APP_ID ? 'Set' : 'Missing',
            }, null, 2)}
          </pre>
        </div>

        <div>
          <Button 
            onClick={handleTestConnectivity} 
            disabled={testing}
            className="w-full"
          >
            {testing ? 'Testing...' : 'Test Firebase Connectivity'}
          </Button>
          
          {connectivity !== null && (
            <div className={`mt-2 p-2 rounded ${connectivity ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
              Firebase connectivity: {connectivity ? 'SUCCESS' : 'FAILED'}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};