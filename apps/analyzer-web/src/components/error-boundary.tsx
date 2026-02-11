"use client";

import { Component, type ErrorInfo, type ReactNode } from "react";
import { Card } from "./ui/card";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("ErrorBoundary caught:", error, info);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;
      return (
        <Card data-testid="error-boundary-fallback" className="text-center py-8">
          <p className="text-red-500 font-semibold mb-2">Something went wrong</p>
          <p className="text-sm text-text-secondary">
            {this.state.error?.message || "An unexpected error occurred"}
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="mt-4 px-4 py-2 rounded-lg bg-accent text-white hover:bg-accent-hover transition-colors text-sm"
          >
            Try again
          </button>
        </Card>
      );
    }
    return this.props.children;
  }
}
