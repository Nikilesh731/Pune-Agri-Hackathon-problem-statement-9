/**
 * Classification Types
 * Purpose: Type definitions for document and data classification
 */

// Basic Classification Types
export interface ClassificationRequest {
  text: string
  categories?: string[]
  threshold?: number
  includeProbabilities?: boolean
  maxResults?: number
}

export interface ClassificationResponse {
  success: boolean
  predictedClass: string
  confidence: number
  probabilities?: Record<string, number>
  processingTimeMs: number
  model?: string
  version?: string
}

// Multi-label Classification Types
export interface MultiLabelClassificationRequest {
  text: string
  categories: string[]
  threshold?: number
  maxLabels?: number
  strategy?: 'independent' | 'hierarchical' | 'exclusive'
}

export interface MultiLabelClassificationResponse {
  success: boolean
  predictedLabels: PredictedLabel[]
  confidence: number
  processingTimeMs: number
  model?: string
  version?: string
}

export interface PredictedLabel {
  label: string
  confidence: number
  probability: number
  reasoning?: string
}

// Hierarchical Classification Types
export interface HierarchicalClassificationRequest {
  text: string
  hierarchy: ClassificationHierarchy
  targetLevel?: number
  includePath?: boolean
}

export interface ClassificationHierarchy {
  levels: ClassificationLevel[]
  relationships: HierarchyRelationship[]
}

export interface ClassificationLevel {
  id: string
  name: string
  depth: number
  categories: string[]
  parent?: string
  children?: string[]
}

export interface HierarchyRelationship {
  parent: string
  child: string
  weight?: number
  condition?: string
}

export interface HierarchicalClassificationResponse {
  success: boolean
  classificationPath: ClassificationPath[]
  confidence: number
  processingTimeMs: number
  alternativePaths?: ClassificationPath[]
}

export interface ClassificationPath {
  level: number
  category: string
  confidence: number
  parent?: string
  children?: string[]
}

// Text Classification Types
export interface TextClassificationRequest {
  text: string
  classificationType: ClassificationType
  language?: string
  domain?: string
  context?: Record<string, any>
}

export enum ClassificationType {
  SENTIMENT = 'sentiment',
  INTENT = 'intent',
  TOPIC = 'topic',
  LANGUAGE = 'language',
  GENRE = 'genre',
  PRIORITY = 'priority',
  CATEGORY = 'category',
  CUSTOM = 'custom'
}

export interface TextClassificationResponse {
  success: boolean
  classification: TextClassification
  confidence: number
  processingTimeMs: number
  features?: TextualFeatures
  metadata?: Record<string, any>
}

export interface TextClassification {
  type: ClassificationType
  result: string | string[]
  sentiment?: SentimentAnalysis
  intent?: IntentAnalysis
  topics?: TopicAnalysis
  language?: LanguageAnalysis
}

export interface SentimentAnalysis {
  polarity: 'positive' | 'negative' | 'neutral'
  subjectivity: 'objective' | 'subjective'
  confidence: number
  score: number
  emotions?: EmotionAnalysis
}

export interface EmotionAnalysis {
  primary: string
  secondary?: string
  confidence: number
  scores: Record<string, number>
}

export interface IntentAnalysis {
  intent: string
  confidence: number
  entities?: EntityExtraction[]
  actions?: ActionExtraction[]
}

export interface EntityExtraction {
  text: string
  type: string
  confidence: number
  start: number
  end: number
  attributes?: Record<string, any>
}

export interface ActionExtraction {
  action: string
  confidence: number
  parameters?: Record<string, any>
  timestamp?: string
}

export interface TopicAnalysis {
  topics: Topic[]
  dominantTopic: string
  coherence: number
  diversity: number
}

export interface Topic {
  name: string
  weight: number
  keywords: string[]
  confidence: number
}

export interface LanguageAnalysis {
  language: string
  confidence: number
  script?: string
  dialect?: string
  alternatives?: LanguageAlternative[]
}

export interface LanguageAlternative {
  language: string
  confidence: number
  script?: string
}

// Image Classification Types
export interface ImageClassificationRequest {
  imageData: string // Base64 encoded image
  classificationType: ImageClassificationType
  categories?: string[]
  threshold?: number
  includeFeatures?: boolean
}

export enum ImageClassificationType {
  OBJECT = 'object',
  SCENE = 'scene',
  ACTIVITY = 'activity',
  DOCUMENT_TYPE = 'document_type',
  QUALITY = 'quality',
  CONTENT = 'content',
  CUSTOM = 'custom'
}

export interface ImageClassificationResponse {
  success: boolean
  classification: ImageClassification
  confidence: number
  processingTimeMs: number
  features?: ImageCapture
  metadata?: Record<string, any>
}

export interface ImageClassification {
  type: ImageClassificationType
  result: string | string[]
  objects?: ObjectDetection[]
  scenes?: SceneClassification[]
  quality?: QualityAssessment
  content?: ContentAnalysis
}

export interface ObjectDetection {
  object: string
  confidence: number
  boundingBox: BoundingBox
  attributes?: Record<string, any>
}

export interface SceneClassification {
  scene: string
  confidence: number
  attributes?: Record<string, any>
}

export interface QualityAssessment {
  overall: number
  sharpness: number
  brightness: number
  contrast: number
  noise: number
  artifacts: number
}

export interface ContentAnalysis {
  contentType: string
  confidence: number
  elements: ContentElement[]
}

export interface ContentElement {
  type: string
  confidence: number
  boundingBox: BoundingBox
  attributes?: Record<string, any>
}

export interface BoundingBox {
  x: number
  y: number
  width: number
  height: number
}

// Document Classification Types
export interface DocumentClassificationRequest {
  textContent?: string
  imageData?: string
  metadata?: Record<string, any>
  classificationLevel: DocumentClassificationLevel
  useHybrid?: boolean
}

export enum DocumentClassificationLevel {
  TYPE = 'type',
  CATEGORY = 'category',
  SUBCATEGORY = 'subcategory',
  DOMAIN = 'domain'
}

export interface DocumentClassificationResponse {
  success: boolean
  classification: DocumentClassification
  confidence: number
  processingTimeMs: number
  features?: DocumentFeatures
  reasoning?: ClassificationReasoning
}

export interface DocumentClassification {
  type?: string
  category?: string
  subcategory?: string
  domain?: string
  confidence: number
  path?: string[]
}

export interface DocumentFeatures {
  textualFeatures: TextualFeatures
  visualFeatures?: VisualFeatures
  structuralFeatures?: StructuralFeatures
  metadataFeatures?: MetadataFeatures
}

export interface TextualFeatures {
  keywords: string[]
  phrases: string[]
  patterns: string[]
  language: string
  complexity: number
  readability: number
}

export interface VisualFeatures {
  layout: string
  elements: string[]
  quality: number
  format: string
}

export interface StructuralFeatures {
  sections: number
  paragraphs: number
  tables: number
  lists: number
  headings: number
}

export interface MetadataFeatures {
  fileSize: number
  fileType: string
  creationDate: Date
  modificationDate: Date
  author?: string
}

export interface ClassificationReasoning {
  primaryFactors: string[]
  secondaryFactors: string[]
  confidenceFactors: string[]
  evidence: Evidence[]
  conclusion: string
}

export interface Evidence {
  type: string
  value: string
  confidence: number
  source: string
}

// Classification Model Types
export interface ClassificationModel {
  id: string
  name: string
  type: ClassificationType
  version: string
  categories: string[]
  accuracy: number
  precision: number
  recall: number
  f1Score: number
  createdAt: Date
  updatedAt: Date
  status: ModelStatus
  config: ModelConfig
}

export enum ModelStatus {
  TRAINING = 'training',
  VALIDATING = 'validating',
  DEPLOYED = 'deployed',
  DEPRECATED = 'deprecated',
  FAILED = 'failed'
}

export interface ModelConfig {
  algorithm: string
  parameters: Record<string, any>
  features: string[]
  preprocessing: PreprocessingConfig
  postprocessing: PostprocessingConfig
}

export interface PreprocessingConfig {
  tokenization?: TokenizationConfig
  normalization?: NormalizationConfig
  featureExtraction?: FeatureExtractionConfig
}

export interface TokenizationConfig {
  type: 'word' | 'character' | 'subword'
  language?: string
  lowercase: boolean
  removePunctuation: boolean
  removeStopwords: boolean
}

export interface NormalizationConfig {
  method: 'standard' | 'minmax' | 'robust'
  featureRange?: [number, number]
}

export interface FeatureExtractionConfig {
  method: 'tfidf' | 'bow' | 'word2vec' | 'bert' | 'custom'
  dimensions?: number
  pretrained?: string
}

export interface PostprocessingConfig {
  threshold?: number
  calibration?: boolean
  smoothing?: boolean
  ensemble?: boolean
}

// Classification Evaluation Types
export interface ClassificationEvaluation {
  modelId: string
  dataset: string
  metrics: ClassificationMetrics
  confusionMatrix?: ConfusionMatrix
  perClassMetrics?: PerClassMetrics
  errors: ClassificationError[]
  recommendations: string[]
}

export interface ClassificationMetrics {
  accuracy: number
  precision: number
  recall: number
  f1Score: number
  auc?: number
  logLoss?: number
  crossEntropy?: number
}

export interface ConfusionMatrix {
  matrix: number[][]
  labels: string[]
  normalized?: number[][]
}

export interface PerClassMetrics {
  class: string
  precision: number
  recall: number
  f1Score: number
  support: number
}

export interface ClassificationError {
  type: ErrorType
  description: string
  frequency: number
  examples: string[]
  suggestedFix: string
}

export enum ErrorType {
  FALSE_POSITIVE = 'false_positive',
  FALSE_NEGATIVE = 'false_negative',
  LOW_CONFIDENCE = 'low_confidence',
  MISCLASSIFICATION = 'misclassification',
  PROCESSING_ERROR = 'processing_error'
}
