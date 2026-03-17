export const WebSocketMessageType = {
  // Connection messages
  CONNECTED: "connected",
  DISCONNECTED: "disconnected",
  PING: "ping",
  PONG: "pong",

  // Subscription messages
  SUBSCRIBE: "subscribe",
  UNSUBSCRIBE: "unsubscribe",
  SUBSCRIBED: "subscribed",

  // Experiment messages
  EXPERIMENT_STARTED: "experiment_started",
  EXPERIMENT_COMPLETED: "experiment_completed",
  EXPERIMENT_FAILED: "experiment_failed",
  EXPERIMENT_CANCELLED: "experiment_cancelled",

  // Training messages
  ROUND_STARTED: "round_started",
  ROUND_COMPLETED: "round_completed",
  CLIENT_UPDATE: "client_update",
  AGGREGATION_COMPLETED: "aggregation_completed",

  // Progress messages
  PROGRESS_UPDATE: "progress_update",
  METRICS_UPDATE: "metrics_update",

  // Client messages
  CLIENT_CONNECTED: "client_connected",
  CLIENT_DISCONNECTED: "client_disconnected",
  CLIENT_TRAINING: "client_training",

  // Log messages
  LOG_MESSAGE: "log_message",
  ERROR: "error",
};
