// useMigrations.ts
import { useState, useEffect, useCallback } from "react";
import { getAuth } from "firebase/auth";

interface Migration {
  id: number;
  name: string;
  applied: boolean;
  created_at: string;
}


export const useMigrationProgress = () => {
  const [migrations, setMigrations] = useState<Migration[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 🔑 Get Firebase token
  const getAuthHeader = useCallback(async (): Promise<HeadersInit> => {
    const auth = getAuth();
    const user = auth.currentUser;
    if (!user) {
      throw new Error("User not authenticated");
    }
    const token = await user.getIdToken();
    return {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    };
  }, []);

  // Fetch migrations
  const fetchMigrations = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const headers = await getAuthHeader();
      const res = await fetch("http://localhost:8000/migrations", {
        headers,
      });

      if (!res.ok) {
        throw new Error(`Failed to fetch migrations: ${res.statusText}`);
      }

      const data: Migration[] = await res.json();
      setMigrations(data);
    } catch (err: any) {
      setError(err.message || "Failed to fetch migrations");
    } finally {
      setLoading(false);
    }
  }, [getAuthHeader]);

  // Apply migration
  const applyMigration = useCallback(
    async (migrationId: number) => {
      try {
        const headers = await getAuthHeader();
        const res = await fetch(`http://localhost:8000/migrations/${migrationId}/apply`, {
          method: "POST",
          headers,
        });

        if (!res.ok) {
          throw new Error(`Failed to apply migration: ${res.statusText}`);
        }

        await fetchMigrations(); // refresh list after applying
      } catch (err: any) {
        setError(err.message || "Failed to apply migration");
      }
    },
    [getAuthHeader, fetchMigrations]
  );

  useEffect(() => {
    fetchMigrations();
  }, [fetchMigrations]);

  return { migrations, loading, error, fetchMigrations, applyMigration };
};
