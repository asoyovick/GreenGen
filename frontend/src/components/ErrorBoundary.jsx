import { Component } from "react";

/**
 * Last-resort boundary: a rendering error must not leave a blank page during
 * a demo. The map and chart libraries are the most likely sources of a runtime
 * failure, so offer a reload rather than trying to recover the broken subtree.
 */
export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    // Keep the details in the console for debugging; the UI stays actionable.
    console.error("Global Change Explorer render error", error, info);
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div className="status-screen status-screen--error" role="alert">
        <h1>The explorer hit an unexpected error</h1>
        <p>
          The data are still on disk. Reload the page to try again, or open the
          API health check to confirm the server is running.
        </p>
        <div className="status-screen__actions">
          <button
            type="button"
            className="button button--primary"
            onClick={() => window.location.reload()}
          >
            Reload the explorer
          </button>
          <a className="button" href="/api/health">
            Open API health
          </a>
        </div>
        <details>
          <summary>Technical detail</summary>
          <pre>
            <code>{String(this.state.error?.message || this.state.error)}</code>
          </pre>
        </details>
      </div>
    );
  }
}
