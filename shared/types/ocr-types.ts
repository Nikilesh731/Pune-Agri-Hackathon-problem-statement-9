/**
 * OCR Types
 * Purpose: Type definitions for OCR processing and text extraction
 */

// OCR Request/Response Types
export interface OCRRequest {
  imageData: string // Base64 encoded image
  language?: string
  preprocess?: boolean
  enhanceContrast?: boolean
  removeNoise?: boolean
  deskew?: boolean
  options?: OCROptions
}

export interface OCROptions {
  engine?: OCREngine
  outputFormat?: OutputFormat
  preserveLayout?: boolean
  detectTables?: boolean
  detectHandwriting?: boolean
  confidenceThreshold?: number
}

export enum OCREngine {
  TESSERACT = 'tesseract',
  GOOGLE_VISION = 'google_vision',
  AWS_TEXTRACT = 'aws_textract',
  AZURE_COGNITIVE = 'azure_cognitive',
  CUSTOM = 'custom'
}

export enum OutputFormat {
  TEXT = 'text',
  JSON = 'json',
  HOCR = 'hocr',
  PDF = 'pdf'
}

export interface OCRResponse {
  success: boolean
  extractedText: string
  confidence: number
  languageDetected?: string
  processingTimeMs: number
  requestId: string
  boundingBoxes?: BoundingBox[]
  words?: WordInfo[]
  lines?: LineInfo[]
  paragraphs?: ParagraphInfo[]
  tables?: TableInfo[]
  errors?: OCRError[]
}

export interface BoundingBox {
  x: number
  y: number
  width: number
  height: number
  confidence: number
}

export interface WordInfo {
  text: string
  confidence: number
  boundingBox: BoundingBox
  baseline?: number[]
  fontAttributes?: FontAttributes
}

export interface LineInfo {
  text: string
  confidence: number
  boundingBox: BoundingBox
  words: WordInfo[]
  baseline?: number[]
}

export interface ParagraphInfo {
  text: string
  confidence: number
  boundingBox: BoundingBox
  lines: LineInfo[]
  language?: string
}

export interface TableInfo {
  id: string
  confidence: number
  boundingBox: BoundingBox
  rows: TableRow[]
  headers?: TableRow[]
}

export interface TableRow {
  cells: TableCell[]
  boundingBox?: BoundingBox
}

export interface TableCell {
  text: string
  confidence: number
  boundingBox: BoundingBox
  rowSpan?: number
  colSpan?: number
  isHeader?: boolean
}

export interface FontAttributes {
  family?: string
  size?: number
  style?: 'normal' | 'italic' | 'oblique'
  weight?: 'normal' | 'bold' | 'bolder' | 'lighter'
  color?: string
}

export interface OCRError {
  code: string
  message: string
  severity: 'error' | 'warning' | 'info'
  boundingBox?: BoundingBox
}

// Batch OCR Types
export interface BatchOCRRequest {
  images: OCRRequest[]
  options?: BatchOCROptions
  parallelProcessing?: boolean
  maxConcurrency?: number
}

export interface BatchOCROptions {
  preserveOrder?: boolean
  failFast?: boolean
  aggregateResults?: boolean
  outputFormat?: OutputFormat
}

export interface BatchOCRResponse {
  results: OCRResponse[]
  totalProcessingTimeMs: number
  successCount: number
  failureCount: number
  averageConfidence: number
  errors?: OCRError[]
}

// OCR Quality Assessment Types
export interface OCRQualityAssessment {
  overallScore: number
  readabilityScore: number
  accuracyScore: number
  completenessScore: number
  issues: QualityIssue[]
  recommendations: string[]
}

export interface QualityIssue {
  type: QualityIssueType
  severity: 'low' | 'medium' | 'high' | 'critical'
  description: string
  location?: BoundingBox
  suggestion?: string
}

export enum QualityIssueType {
  LOW_CONFIDENCE = 'low_confidence',
  BLURRY_TEXT = 'blurry_text',
  POOR_LIGHTING = 'poor_lighting',
  SKEWED_IMAGE = 'skewed_image',
  NOISY_BACKGROUND = 'noisy_background',
  SMALL_TEXT = 'small_text',
  HANDWRITING = 'handwriting',
  FOREIGN_LANGUAGE = 'foreign_language',
  TABLE_DETECTION = 'table_detection',
  LAYOUT_ISSUES = 'layout_issues'
}

// OCR Enhancement Types
export interface OCREnhancementRequest {
  imageData: string
  enhancements: EnhancementType[]
  options?: EnhancementOptions
}

export enum EnhancementType {
  DENOISE = 'denoise',
  DESKEW = 'deskew',
  BRIGHTNESS_ADJUST = 'brightness_adjust',
  CONTRAST_ENHANCE = 'contrast_enhance',
  SHARPEN = 'sharpen',
  RESIZE = 'resize',
  BINARIZE = 'binarize',
  REMOVE_BACKGROUND = 'remove_background'
}

export interface EnhancementOptions {
  strength?: number
  preserveOriginal?: boolean
  targetQuality?: number
  outputFormat?: 'png' | 'jpeg' | 'tiff'
}

export interface OCREnhancementResponse {
  success: boolean
  enhancedImageData: string
  originalSize: number
  enhancedSize: number
  processingTimeMs: number
  appliedEnhancements: EnhancementType[]
  qualityImprovement?: number
}

// OCR Template Types
export interface OCRTemplate {
  id: string
  name: string
  documentType: string
  fields: TemplateField[]
  layout?: TemplateLayout
  preprocessing?: PreprocessingConfig
  postprocessing?: PostprocessingConfig
}

export interface TemplateField {
  name: string
  fieldType: FieldType
  required: boolean
  validation?: FieldValidation
  extractionHints?: ExtractionHints
  boundingBox?: BoundingBox
  keywords?: string[]
}

export enum FieldType {
  TEXT = 'text',
  NUMBER = 'number',
  DATE = 'date',
  EMAIL = 'email',
  PHONE = 'phone',
  ADDRESS = 'address',
  AMOUNT = 'amount',
  SELECT = 'select',
  CHECKBOX = 'checkbox'
}

export interface FieldValidation {
  pattern?: string
  minLength?: number
  maxLength?: number
  min?: number
  max?: number
  allowedValues?: string[]
  customValidator?: string
}

export interface ExtractionHints {
  keywords?: string[]
  patterns?: string[]
  context?: string
  examples?: string[]
  priority?: number
}

export interface TemplateLayout {
  type: 'form' | 'table' | 'document' | 'freeform'
  structure?: LayoutStructure
  regions?: Region[]
}

export interface LayoutStructure {
  columns: number
  rows?: number
  header?: boolean
  footer?: boolean
  margins?: Margins
}

export interface Margins {
  top: number
  right: number
  bottom: number
  left: number
}

export interface Region {
  id: string
  type: 'header' | 'footer' | 'body' | 'sidebar' | 'table'
  boundingBox: BoundingBox
  fields?: string[]
}

export interface PreprocessingConfig {
  enhanceContrast: boolean
  removeNoise: boolean
  deskew: boolean
  binarize: boolean
  resize?: ResizeConfig
}

export interface ResizeConfig {
  width?: number
  height?: number
  maintainAspectRatio: boolean
  quality?: number
}

export interface PostprocessingConfig {
  correctSpelling: boolean
  formatNumbers: boolean
  standardizeDates: boolean
  validateFields: boolean
}

// OCR Analytics Types
export interface OCRAnalytics {
  totalDocuments: number
  successRate: number
  averageConfidence: number
  averageProcessingTime: number
  errorDistribution: Record<string, number>
  qualityDistribution: Record<string, number>
  languageDistribution: Record<string, number>
  templateUsage: Record<string, number>
}

export interface OCRPerformanceMetrics {
  processingTime: number
  memoryUsage: number
  cpuUsage: number
  accuracy: number
  throughput: number
  errorRate: number
}
