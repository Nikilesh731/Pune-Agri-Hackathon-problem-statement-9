import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { 
  FileText, 
  CheckCircle, 
  Clock, 
  AlertTriangle,
  ArrowRight,
  Zap,
  Shield,
  Target,
  Brain
} from 'lucide-react'
import { FileUpload } from '../components/FileUpload'
import { PageHeader } from '../../../components/ui/PageHeader'
import { SectionCard } from '../../../components/ui/SectionCard'
import { Button } from '../../../components/ui/Button'

export const UploadPage: React.FC = () => {
  const navigate = useNavigate()
  const [successMessage, setSuccessMessage] = useState<{ 
    text: string; 
    applicationId?: string; 
    isReupload?: boolean;
    parentApplicationId?: string;
  } | null>(null)
  const [errorMessage, setErrorMessage] = useState<{ 
    type: 'error' | 'duplicate_blocked';
    message: string; 
    existingApplicationId?: string;
  } | null>(null)
  const [uploadComplete, setUploadComplete] = useState(false)
  const [isUploading, setIsUploading] = useState(false)

  const handleUploadSuccess = (response: any) => {
    // Handle different response scenarios
    if (response.status === 'duplicate_blocked') {
      // SCENARIO A: Blocked duplicate
      setErrorMessage({
        type: 'duplicate_blocked',
        message: response.message,
        existingApplicationId: response.existingApplicationId
      })
      setSuccessMessage(null)
      setUploadComplete(false)
      setIsUploading(false)
    } else if (response.status === 'reupload_allowed') {
      // SCENARIO B: Re-upload allowed
      setSuccessMessage({
        text: response.message,
        applicationId: response.application?.id,
        isReupload: true,
        parentApplicationId: response.parentApplicationId
      })
      setErrorMessage(null)
      setUploadComplete(true)
      setIsUploading(false)
    } else {
      // SCENARIO C: Normal upload success
      setSuccessMessage({
        text: response.message || 'Document uploaded successfully! AI processing has begun.',
        applicationId: response.application?.id,
        isReupload: false
      })
      setErrorMessage(null)
      setUploadComplete(true)
      setIsUploading(false)
    }
  }

  const handleUploadError = (error: any) => {
    // Handle different error types
    if (error.status === 'duplicate_blocked') {
      // Duplicate blocked error
      setErrorMessage({
        type: 'duplicate_blocked',
        message: error.message,
        existingApplicationId: error.existingApplicationId
      })
    } else {
      // Regular error
      setErrorMessage({
        type: 'error',
        message: typeof error === 'string' ? error : error.message || 'Upload failed'
      })
    }
    setSuccessMessage(null)
    setUploadComplete(false)
    setIsUploading(false)
  }

  const resetUpload = () => {
    setSuccessMessage(null)
    setErrorMessage(null)
    setUploadComplete(false)
    setIsUploading(false)
  }

  const processingSteps = [
    { icon: FileText, title: 'OCR Processing', desc: 'Text extraction & analysis', color: 'blue' },
    { icon: Brain, title: 'AI Classification', desc: 'Document type identification', color: 'purple' },
    { icon: Zap, title: 'Field Extraction', desc: 'Structured data extraction', color: 'green' },
    { icon: Shield, title: 'Fraud Detection', desc: 'Risk assessment & validation', color: 'red' },
    { icon: Target, title: 'Smart Routing', desc: 'Priority scoring & assignment', color: 'orange' }
  ]

  return (
    <div>
      <PageHeader 
        title="Smart Document Intake"
        subtitle="AI-powered agricultural document processing with instant insights"
      />

      {/* Success Message */}
      {successMessage && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <SectionCard title={successMessage.isReupload ? "Re-upload Accepted" : "Success"}>
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  {successMessage.isReupload ? (
                    <ArrowRight className="h-6 w-6 text-blue-600" />
                  ) : (
                    <CheckCircle className="h-6 w-6 text-green-600" />
                  )}
                </div>
                <div className="ml-3">
                  <h3 className={`text-sm font-medium ${successMessage.isReupload ? 'text-blue-800' : 'text-green-800'}`}>
                    {successMessage.isReupload ? 'Re-upload Successful' : 'Upload Successful'}
                  </h3>
                  <p className={`text-sm ${successMessage.isReupload ? 'text-blue-700' : 'text-green-700'}`}>
                    {successMessage.text}
                  </p>
                  {successMessage.isReupload && successMessage.parentApplicationId && (
                    <p className="text-xs text-blue-600 mt-1">
                      Previous application: {successMessage.parentApplicationId.slice(0, 8)}...
                    </p>
                  )}
                </div>
              </div>
              <div className="flex items-center space-x-3">
                {successMessage?.applicationId && (
                  <Button
                    variant={successMessage.isReupload ? "secondary" : "success"}
                    onClick={() => navigate(`/applications/${successMessage.applicationId}`)}
                  >
                    {successMessage.isReupload ? 'Track New Version' : 'Track Case'}
                  </Button>
                )}
                <Button variant="secondary" onClick={resetUpload}>
                  Upload Another
                </Button>
              </div>
            </div>
          </SectionCard>
        </motion.div>
      )}

      {/* Error Message */}
      {errorMessage && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <SectionCard title={errorMessage.type === 'duplicate_blocked' ? 'Duplicate Blocked' : 'Error'}>
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  {errorMessage.type === 'duplicate_blocked' ? (
                    <AlertTriangle className="h-6 w-6 text-red-600" />
                  ) : (
                    <AlertTriangle className="h-6 w-6 text-orange-600" />
                  )}
                </div>
                <div className="ml-3">
                  <h3 className={`text-sm font-medium ${errorMessage.type === 'duplicate_blocked' ? 'text-red-800' : 'text-orange-800'}`}>
                    {errorMessage.type === 'duplicate_blocked' ? 'Duplicate Document Blocked' : 'Upload Failed'}
                  </h3>
                  <p className={`text-sm ${errorMessage.type === 'duplicate_blocked' ? 'text-red-700' : 'text-orange-700'}`}>
                    {errorMessage.message}
                  </p>
                  {errorMessage.type === 'duplicate_blocked' && errorMessage.existingApplicationId && (
                    <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs">
                      <p className="text-red-800 font-medium mb-1">Existing Application:</p>
                      <p className="text-red-600 font-mono">CASE-{errorMessage.existingApplicationId.slice(0, 8)}...</p>
                      <p className="text-red-600 mt-1">This document is already under processing.</p>
                    </div>
                  )}
                </div>
              </div>
              <div className="flex items-center space-x-3">
                {errorMessage.type === 'duplicate_blocked' && errorMessage.existingApplicationId && (
                  <Button
                    variant="secondary"
                    onClick={() => navigate(`/applications/${errorMessage.existingApplicationId}`)}
                  >
                    View Existing
                  </Button>
                )}
                <Button variant="secondary" onClick={resetUpload}>
                  {errorMessage.type === 'duplicate_blocked' ? 'Upload Different Document' : 'Try Again'}
                </Button>
              </div>
            </div>
          </SectionCard>
        </motion.div>
      )}

      {!uploadComplete ? (
        <div className="space-y-8">
          {/* Upload Section */}
          <SectionCard title="Document Upload">
            <div className="space-y-6">
              {/* Supported Document Types */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Supported Document Types</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {[
                    { icon: '📋', name: 'Scheme Applications', desc: 'Government scheme forms' },
                    { icon: '💰', name: 'Subsidy Claims', desc: 'Financial assistance requests' },
                    { icon: '🛡️', name: 'Insurance Claims', desc: 'Crop insurance documents' },
                    { icon: '✉️', name: 'Grievance Letters', desc: 'Complaints & appeals' },
                    { icon: '👨‍🌾', name: 'Farmer Records', desc: 'Personal & farm details' },
                    { icon: '📊', name: 'Land Records', desc: 'Property & ownership docs' }
                  ].map((doc, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: index * 0.1 }}
                      className="flex items-center p-3 border border-gray-200 rounded-lg hover:border-green-300 hover:bg-green-50 transition-colors"
                    >
                      <span className="text-2xl mr-3">{doc.icon}</span>
                      <div>
                        <div className="font-medium text-gray-900">{doc.name}</div>
                        <div className="text-sm text-gray-500">{doc.desc}</div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>

              {/* AI Processing Info */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start">
                  <Brain className="h-5 w-5 text-blue-600 mt-0.5 mr-3" />
                  <div>
                    <h4 className="text-sm font-medium text-blue-900 mb-1">AI-Powered Processing</h4>
                    <p className="text-sm text-blue-700">
                      Documents undergo automatic classification, field extraction, fraud detection, and priority scoring. 
                      Processing typically takes 2-5 minutes.
                    </p>
                  </div>
                </div>
              </div>

              {/* File Upload Component */}
              <div className="border-t pt-6">
                <FileUpload
                  onUploadSuccess={handleUploadSuccess}
                  onUploadError={handleUploadError}
                />
              </div>

              {/* Upload Guidelines */}
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <h4 className="text-sm font-medium text-gray-900 mb-2">Upload Guidelines</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• Supported formats: PDF, JPG, PNG, DOC, DOCX</li>
                  <li>• Maximum file size: 10MB per document</li>
                  <li>• Ensure documents are clear and legible</li>
                  <li>• Include all required signatures and stamps</li>
                </ul>
              </div>
            </div>
          </SectionCard>

          {/* Processing Pipeline Preview */}
          <SectionCard title="AI Processing Pipeline">
            <div className="space-y-4">
              <p className="text-sm text-gray-600">
                Your document will be processed through our advanced AI pipeline to extract insights and ensure quality.
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                {processingSteps.map((step, index) => {
                  const Icon = step.icon
                  return (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="text-center"
                    >
                      <div className={`w-12 h-12 bg-${step.color}-100 rounded-full flex items-center justify-center mx-auto mb-2`}>
                        <Icon className={`w-6 h-6 text-${step.color}-600`} />
                      </div>
                      <h4 className="text-xs font-medium text-gray-900">{step.title}</h4>
                      <p className="text-xs text-gray-500">{step.desc}</p>
                    </motion.div>
                  )
                })}
              </div>

              {isUploading && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="text-center py-4"
                >
                  <div className="inline-flex items-center px-4 py-2 bg-blue-100 text-blue-800 rounded-full">
                    <Clock className="w-4 h-4 mr-2 animate-spin" />
                    AI processing in progress...
                  </div>
                </motion.div>
              )}
            </div>
          </SectionCard>
        </div>
      ) : (
        /* Upload Complete State */
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <SectionCard title="Processing Underway">
            <div className="text-center py-8">
              <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-green-100 mb-6">
                <CheckCircle className="h-8 w-8 text-green-600" />
              </div>
              
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                AI Processing Started!
              </h3>
              <p className="text-gray-600 mb-6 max-w-2xl mx-auto">
                Your document is now being processed through our AI pipeline. You'll receive intelligent insights, 
                completeness scores, and officer recommendations automatically.
              </p>
              
              {/* Case Reference */}
              {successMessage?.applicationId && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 max-w-md mx-auto">
                  <h4 className="text-sm font-medium text-blue-900 mb-1">Case Reference</h4>
                  <p className="text-lg font-mono text-blue-800">
                    CASE-{successMessage.applicationId.slice(0, 8)}...
                  </p>
                  <p className="text-xs text-blue-600 mt-1">Save this reference for tracking</p>
                </div>
              )}
              
              {/* Action Buttons */}
              <div className="flex justify-center space-x-4">
                {successMessage?.applicationId && (
                  <Button
                    variant="success"
                    onClick={() => navigate(`/applications/${successMessage.applicationId}`)}
                  >
                    Track Processing
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                )}
                <Button
                  variant="secondary"
                  onClick={() => navigate('/applications')}
                >
                  View Cases
                </Button>
                <Button
                  variant="secondary"
                  onClick={resetUpload}
                >
                  Upload Another
                </Button>
              </div>
              
              {/* Processing Status */}
              <div className="mt-8 p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-center space-x-2 text-sm text-gray-600">
                  <Clock className="w-4 h-4" />
                  <span>Estimated processing time: 2-5 minutes</span>
                </div>
              </div>
            </div>
          </SectionCard>
        </motion.div>
      )}
    </div>
  )
}
