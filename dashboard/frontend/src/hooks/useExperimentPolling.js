import { useState, useEffect, useCallback, useRef } from "react";
import { experimentService } from "../services/api";

export const useExperimentPolling = (experimentId, options = {}) => {
  const {
    interval = 2000, // Poll every 2 seconds
    enabled = true,
    onProgressUpdate,
    onComplete,
    onError,
  } = options;

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isPolling, setIsPolling] = useState(false);

  const pollingRef = useRef(null);
  const lastStatusRef = useRef(null);

  const fetchProgress = useCallback(async () => {
    if (!experimentId) return;

    try {
      setLoading(false);
      const response = await experimentService.getProgress(experimentId);

      const newData = response.data;
      setData(newData);

      // Check for status changes
      if (lastStatusRef.current !== newData.status) {
        if (newData.status === "completed") {
          onComplete?.(newData);
          stopPolling();
        }
        lastStatusRef.current = newData.status;
      }

      // Call progress update callback
      onProgressUpdate?.(newData);

      setError(null);
    } catch (err) {
      console.error("Error polling experiment progress:", err);
      setError(err.message);
      onError?.(err);
    }
  }, [experimentId, onProgressUpdate, onComplete, onError]);

  const startPolling = useCallback(() => {
    if (pollingRef.current || !enabled) return;

    setIsPolling(true);
    // Fetch immediately
    fetchProgress();

    // Set up interval
    pollingRef.current = setInterval(fetchProgress, interval);
  }, [fetchProgress, interval, enabled]);

  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
      setIsPolling(false);
    }
  }, []);

  // Start/stop polling based on enabled state
  useEffect(() => {
    if (enabled && experimentId) {
      startPolling();
    } else {
      stopPolling();
    }

    return () => stopPolling();
  }, [enabled, experimentId, startPolling, stopPolling]);

  // Manual refresh function
  const refresh = useCallback(async () => {
    stopPolling();
    await fetchProgress();
    if (enabled) {
      startPolling();
    }
  }, [fetchProgress, startPolling, stopPolling, enabled]);

  return {
    data,
    loading,
    error,
    isPolling,
    refresh,
    stopPolling,
    startPolling,
  };
};
