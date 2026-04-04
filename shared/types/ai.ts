/**
 * AI Service Types
 * Purpose: Main orchestrator for AI service type definitions
 */

// Re-export all types from specialized modules with explicit names to avoid conflicts
export {
  FieldValidation,
  ClassificationReasoning,
  DocumentClassificationRequest,
  DocumentClassificationResponse,
  DocumentType,
  ExtractionResult,
  ValidationResult,
  DocumentMetadata,
  ProcessingStatus
} from './document-types';

export {
  BoundingBox,
  PreprocessingConfig,
  PostprocessingConfig,
  OCRRequest,
  OCRResponse,
  OCREngine,
  OutputFormat,
  OCROptions,
  WordInfo,
  LineInfo,
  ParagraphInfo,
  TableInfo,
  FontAttributes,
  OCRError,
  BatchOCRRequest,
  BatchOCROptions,
  BatchOCRResponse,
  OCRQualityAssessment,
  QualityIssue,
  QualityIssueType,
  OCREnhancementRequest,
  EnhancementType,
  EnhancementOptions,
  OCREnhancementResponse,
  OCRTemplate,
  TemplateField,
  FieldType,
  ExtractionHints,
  TemplateLayout,
  LayoutStructure,
  Margins,
  Region,
  ResizeConfig,
  OCRAnalytics,
  OCRPerformanceMetrics
} from './ocr-types';

export {
  ClassificationRequest,
  ClassificationResponse,
  MultiLabelClassificationRequest,
  MultiLabelClassificationResponse,
  PredictedLabel,
  HierarchicalClassificationRequest,
  ClassificationHierarchy,
  ClassificationLevel,
  HierarchyRelationship,
  HierarchicalClassificationResponse,
  ClassificationPath,
  TextClassificationRequest,
  ClassificationType,
  TextClassificationResponse,
  TextClassification,
  SentimentAnalysis,
  EmotionAnalysis,
  IntentAnalysis,
  EntityExtraction,
  ActionExtraction,
  TopicAnalysis,
  Topic,
  LanguageAnalysis,
  LanguageAlternative,
  ImageClassificationRequest,
  ImageClassificationType,
  ImageClassificationResponse,
  ImageClassification,
  ObjectDetection,
  SceneClassification,
  QualityAssessment,
  ContentAnalysis,
  ContentElement,
  DocumentClassificationLevel,
  DocumentClassification,
  DocumentFeatures,
  TextualFeatures,
  VisualFeatures,
  StructuralFeatures,
  MetadataFeatures,
  Evidence,
  ClassificationModel,
  ModelStatus,
  ModelConfig,
  PreprocessingConfig as ClassificationPreprocessingConfig,
  TokenizationConfig,
  NormalizationConfig,
  FeatureExtractionConfig
} from './classification-types';

// Additional AI Service Types that don't fit in specific modules
export interface AIServiceConfig {
  name: string
  version: string
  endpoint: string
  apiKey?: string
  timeout: number
  retryAttempts: number
  rateLimit?: RateLimit
}

export interface RateLimit {
  requestsPerSecond: number
  requestsPerMinute: number
  requestsPerHour: number
  burstLimit: number
}

export interface AIServiceResponse<T = any> {
  success: boolean
  data?: T
  error?: AIServiceError
  metadata?: ResponseMetadata
  requestId: string
  processingTimeMs: number
}

export interface AIServiceError {
  code: string
  message: string
  details?: Record<string, any>
  retryable: boolean
  suggestedAction?: string
}

export interface ResponseMetadata {
  model?: string
  version?: string
  confidence?: number
  tokens?: TokenUsage
  cost?: number
}

export interface TokenUsage {
  input: number
  output: number
  total: number
}

// AI Service Health Types
export interface AIServiceHealth {
  service: string
  status: HealthStatus
  uptime: number
  responseTime: number
  errorRate: number
  lastCheck: Date
  dependencies?: ServiceDependency[]
}

export enum HealthStatus {
  HEALTHY = 'healthy',
  DEGRADED = 'degraded',
  UNHEALTHY = 'unhealthy',
  UNKNOWN = 'unknown'
}

export interface ServiceDependency {
  name: string
  status: HealthStatus
  responseTime?: number
  lastCheck?: Date
}

// AI Service Analytics Types
export interface AIServiceAnalytics {
  service: string
  period: AnalyticsPeriod
  metrics: ServiceMetrics
  performance: PerformanceMetrics
  usage: UsageMetrics
  costs: CostMetrics
}

export enum AnalyticsPeriod {
  HOUR = 'hour',
  DAY = 'day',
  WEEK = 'week',
  MONTH = 'month',
  YEAR = 'year'
}

export interface ServiceMetrics {
  totalRequests: number
  successfulRequests: number
  failedRequests: number
  averageResponseTime: number
  p95ResponseTime: number
  p99ResponseTime: number
  errorRate: number
  throughput: number
}

export interface PerformanceMetrics {
  cpuUsage: number
  memoryUsage: number
  diskUsage: number
  networkIO: number
  gpuUsage?: number
}

export interface UsageMetrics {
  requestsByEndpoint: Record<string, number>
  requestsByUser: Record<string, number>
  requestsByRegion: Record<string, number>
  peakUsage: PeakUsage
}

export interface PeakUsage {
  timestamp: Date
  requestsPerSecond: number
  concurrentUsers: number
}

export interface CostMetrics {
  totalCost: number
  costPerRequest: number
  costByEndpoint: Record<string, number>
  costByUser: Record<string, number>
  tokenCosts: TokenCosts
}

export interface TokenCosts {
  inputTokenCost: number
  outputTokenCost: number
  totalTokenCost: number
  tokensProcessed: number
}

// AI Service Configuration Types
export interface AIServiceDeployment {
  service: string
  environment: DeploymentEnvironment
  version: string
  config: DeploymentConfig
  resources: ResourceConfig
  scaling: ScalingConfig
}

export enum DeploymentEnvironment {
  DEVELOPMENT = 'development',
  STAGING = 'staging',
  PRODUCTION = 'production',
  TESTING = 'testing'
}

export interface DeploymentConfig {
  replicas: number
  resources: ResourceRequirements
  environment: Record<string, string>
  secrets: Record<string, string>
  volumes?: VolumeConfig[]
}

export interface ResourceRequirements {
  cpu: string
  memory: string
  gpu?: string
  storage?: string
}

export interface VolumeConfig {
  name: string
  path: string
  size: string
  type: 'persistent' | 'ephemeral' | 'shared'
}

export interface ResourceConfig {
  limits: ResourceRequirements
  requests: ResourceRequirements
}

export interface ScalingConfig {
  minReplicas: number
  maxReplicas: number
  targetCPUUtilization?: number
  targetMemoryUtilization?: number
  scalingPolicy?: ScalingPolicy[]
}

export interface ScalingPolicy {
  type: 'horizontal' | 'vertical'
  trigger: ScalingTrigger
  action: ScalingAction
  cooldown: number
}

export interface ScalingTrigger {
  metric: string
  threshold: number
  operator: 'gt' | 'lt' | 'eq'
  duration: number
}

export interface ScalingAction {
  type: 'scale_up' | 'scale_down'
  replicas?: number
  resources?: ResourceRequirements
}

// AI Service Monitoring Types
export interface AIServiceMonitoring {
  service: string
  alerts: ServiceAlert[]
  logs: ServiceLog[]
  traces: ServiceTrace[]
  metrics: ServiceMetrics
}

export interface ServiceAlert {
  id: string
  severity: AlertSeverity
  type: AlertType
  message: string
  timestamp: Date
  resolved: boolean
  resolvedAt?: Date
  metadata?: Record<string, any>
}

export enum AlertSeverity {
  CRITICAL = 'critical',
  WARNING = 'warning',
  INFO = 'info',
  DEBUG = 'debug'
}

export enum AlertType {
  ERROR_RATE = 'error_rate',
  RESPONSE_TIME = 'response_time',
  RESOURCE_USAGE = 'resource_usage',
  AVAILABILITY = 'availability',
  COST = 'cost',
  SECURITY = 'security'
}

export interface ServiceLog {
  id: string
  timestamp: Date
  level: LogLevel
  message: string
  service: string
  requestId?: string
  userId?: string
  metadata?: Record<string, any>
  stackTrace?: string
}

export enum LogLevel {
  ERROR = 'error',
  WARN = 'warn',
  INFO = 'info',
  DEBUG = 'debug'
}

export interface ServiceTrace {
  id: string
  timestamp: Date
  duration: number
  service: string
  operation: string
  status: TraceStatus
  spans: TraceSpan[]
  metadata?: Record<string, any>
}

export enum TraceStatus {
  SUCCESS = 'success',
  ERROR = 'error',
  TIMEOUT = 'timeout',
  CANCELLED = 'cancelled'
}

export interface TraceSpan {
  id: string
  parentSpanId?: string
  operation: string
  startTime: Date
  endTime: Date
  duration: number
  status: TraceStatus
  tags?: Record<string, string>
  logs?: ServiceLog[]
}

// AI Service Security Types
export interface AIServiceSecurity {
  service: string
  authentication: AuthenticationConfig
  authorization: AuthorizationConfig
  encryption: EncryptionConfig
  audit: AuditConfig
}

export interface AuthenticationConfig {
  type: 'api_key' | 'oauth' | 'jwt' | 'basic'
  config: Record<string, any>
  enabled: boolean
}

export interface AuthorizationConfig {
  type: 'rbac' | 'abac' | 'custom'
  policies: AuthorizationPolicy[]
  enabled: boolean
}

export interface AuthorizationPolicy {
  id: string
  name: string
  rules: AuthorizationRule[]
  effect: 'allow' | 'deny'
}

export interface AuthorizationRule {
  action: string
  resource: string
  condition?: string
  effect: 'allow' | 'deny'
}

export interface EncryptionConfig {
  atRest: boolean
  inTransit: boolean
  algorithm: string
  keyRotation: KeyRotationConfig
}

export interface KeyRotationConfig {
  enabled: boolean
  interval: number
  nextRotation?: Date
}

export interface AuditConfig {
  enabled: boolean
  events: AuditEvent[]
  retention: RetentionConfig
}

export interface AuditEvent {
  type: string
  enabled: boolean
  fields: string[]
}

export interface RetentionConfig {
  days: number
  autoDelete: boolean
}

// AI Service Testing Types
export interface AIServiceTest {
  service: string
  testSuite: TestSuite
  results: TestResults
  coverage: TestCoverage
}

export interface TestSuite {
  name: string
  version: string
  tests: TestCase[]
  environment: DeploymentEnvironment
}

export interface TestCase {
  id: string
  name: string
  type: TestType
  input: any
  expectedOutput: any
  timeout: number
  retries: number
}

export enum TestType {
  UNIT = 'unit',
  INTEGRATION = 'integration',
  E2E = 'e2e',
  PERFORMANCE = 'performance',
  SECURITY = 'security'
}

export interface TestResults {
  total: number
  passed: number
  failed: number
  skipped: number
  duration: number
  successRate: number
  failures: TestFailure[]
}

export interface TestFailure {
  testId: string
  testName: string
  error: string
  stackTrace?: string
  duration: number
}

export interface TestCoverage {
  lines: number
  functions: number
  branches: number
  statements: number
  percentage: number
}
