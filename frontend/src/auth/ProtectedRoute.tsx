import type { ReactNode } from "react";
import { Navigate } from "react-router";

import { useAuth } from "./useAuth";

interface ProtectedRouteProps {
    children: ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
    const { user, isLoading } = useAuth();
    
    if (isLoading) {
        return <p>Loading...</p>
    }

    if (!user) {
        return <Navigate to="/login" replace />;
    }

    return children;
}