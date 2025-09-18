import { useState } from 'react';
import { SignIn } from '@/components/auth/SignIn';
import { SignUp } from '@/components/auth/SignUp';

export const Auth = () => {
  const [isSignIn, setIsSignIn] = useState(true);

  const toggleMode = () => {
    setIsSignIn(!isSignIn);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="w-full max-w-md">
        {isSignIn ? (
          <SignIn onToggleMode={toggleMode} />
        ) : (
          <SignUp onToggleMode={toggleMode} />
        )}
      </div>
    </div>
  );
};