import { useState } from 'react'
import { MappedApplication, normalizePriorityScore } from '../../utils/applicationDetailMapper'
import { SectionCard } from '../ui/SectionCard'
import { StatusBadge } from '../ui/StatusBadge'
import { ChevronDownIcon, ChevronRightIcon } from '@heroicons/react/24/outline'
import { applicationsService } from '../../services/applicationsService'

interface ApplicationSectionsProps {
  application?: MappedApplication
}

export function ApplicationSections({ application }: ApplicationSectionsProps) {
  if (!application) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500">Application data not available</p>
      </div>
    )
  }

  // Use only normalized/mapped data
  const normalizedData = (application as any).normalizedData || {}
  const extractedFields = normalizedData.extractedFields || {}

  if (!normalizedData || Object.keys(normalizedData).length === 0) {
    return <div className="text-gray-500">No processed data available</div>
  }

  const [mlInsightsOpen, setMlInsightsOpen] = useState(false)
  const [loadingFileUrl, setLoadingFileUrl] = useState(false)


  const humanizeKey = (key: string) => {
    return String(key)
      .replace(/([A-Z])/g, ' $1')
      .replace(/_/g, ' ')
      .replace(/\b\w/g, l => l.toUpperCase())
      .trim()
  }

  const handleViewDocument = async (doc: any) => {
    if (doc?.url) {
      if (doc.url.startsWith('http://') || doc.url.startsWith('https://')) {
        window.open(doc.url, '_blank', 'noopener,noreferrer')
        return
      }
      try {
        setLoadingFileUrl(true)
        const response = await applicationsService.getFileUrlByPath(doc.url)
        window.open(response.fileUrl, '_blank', 'noopener,noreferrer')
      } catch (err) {
        console.error('Failed to open document', err)
        alert('Failed to open document')
      } finally {
        setLoadingFileUrl(false)
      }
    }
  }

  // Missing fields: hide ones that are present in extractedFields
  const rawMissing = normalizedData.missingFields || []
  const missingFields = rawMissing.filter((f: string) => {
    const k = String(f).replace(/_/g, '').toLowerCase()
    return !Object.keys(extractedFields).some(ek => ek.replace(/_/g, '').toLowerCase() === k && extractedFields[ek])
  })

  // Officer summary: prefer backend aiSummary, fallback to decision support reasoning
  const summary =
    application.aiSummary ||
    application.extractedData?.decision_support?.reasoning?.[0] ||
    "No summary available"

  const hasMlInsights = normalizedData.mlInsights && Object.keys(normalizedData.mlInsights).length > 0
  const hasDecisionSupport = !!normalizedData.decisionSupport
  const hasRiskFlags = (normalizedData.riskFlags || []).length > 0
  const hasExtracted = Object.keys(extractedFields).length > 0

  const formatDocLabel = (type: string) => {
    if (!type) return 'Unknown'
    return String(type).replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())
  }

  return (
    <div className="space-y-6">
      {/* 1. Officer Summary (TOP) */}
      <SectionCard title="Officer Summary">
        <div className="space-y-3">
          <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
            <div className="text-sm text-gray-700">
              {summary}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {normalizedData.confidenceScore > 0 && (
              <div className="text-center p-3 bg-white rounded-lg border">
                <div className="text-2xl font-bold text-gray-900">{Math.round(normalizedData.confidenceScore)}%</div>
                <div className="text-xs text-gray-600">Confidence</div>
              </div>
            )}
            {normalizedData.completenessScore > 0 && (
              <div className="text-center p-3 bg-white rounded-lg border">
                <div className="text-2xl font-bold text-gray-900">{Math.round(normalizedData.completenessScore)}%</div>
                <div className="text-xs text-gray-600">Completeness</div>
              </div>
            )}
            {normalizedData.priorityScore !== undefined && (
              <div className="text-center p-3 bg-white rounded-lg border">
                <div className="text-2xl font-bold text-gray-900">{normalizePriorityScore(normalizedData.priorityScore)}%</div>
                <div className="text-xs text-gray-600">Priority</div>
              </div>
            )}
          </div>
        </div>
      </SectionCard>

      {/* 2. Extracted Information (expanded) */}
      <SectionCard title={
        <div className="flex items-center justify-between w-full">
          <span className="font-semibold">Extracted Information</span>
          <span className="text-sm text-gray-400">{formatDocLabel(application.type || '')}</span>
        </div>
      }>
        <div className="space-y-4">
          {hasExtracted ? (
            <div>
              <h4 className="text-md font-medium text-gray-900 mb-3">Personal Information</h4>
              <dl className="grid grid-cols-1 gap-x-4 gap-y-3 sm:grid-cols-2">
                {extractedFields.farmerName && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Farmer Name</dt>
                    <dd className="mt-1 text-sm text-gray-900">{extractedFields.farmerName}</dd>
                  </div>
                )}
                {extractedFields.guardianName && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Guardian Name</dt>
                    <dd className="mt-1 text-sm text-gray-900">{extractedFields.guardianName}</dd>
                  </div>
                )}
                {extractedFields.aadhaarNumber && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Aadhaar Number</dt>
                    <dd className="mt-1 text-sm text-gray-900">{extractedFields.aadhaarNumber}</dd>
                  </div>
                )}
                {extractedFields.mobileNumber && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Mobile Number</dt>
                    <dd className="mt-1 text-sm text-gray-900">{extractedFields.mobileNumber}</dd>
                  </div>
                )}
                {extractedFields.address && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Address</dt>
                    <dd className="mt-1 text-sm text-gray-900">{extractedFields.address}</dd>
                  </div>
                )}
                {extractedFields.village && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Village</dt>
                    <dd className="mt-1 text-sm text-gray-900">{extractedFields.village}</dd>
                  </div>
                )}
                {extractedFields.district && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">District</dt>
                    <dd className="mt-1 text-sm text-gray-900">{extractedFields.district}</dd>
                  </div>
                )}
              </dl>

              {/* Financial */}
              {(extractedFields.annualIncome || extractedFields.requestedAmount) && (
                <div className="mt-4">
                  <h4 className="text-md font-medium text-gray-900 mb-3">Financial Information</h4>
                  <dl className="grid grid-cols-1 gap-x-4 gap-y-3 sm:grid-cols-2">
                    {extractedFields.annualIncome && (
                      <div>
                        <dt className="text-sm font-medium text-gray-500">Annual Income</dt>
                        <dd className="mt-1 text-sm text-gray-900">{extractedFields.annualIncome}</dd>
                      </div>
                    )}
                    {extractedFields.requestedAmount && (
                      <div>
                        <dt className="text-sm font-medium text-gray-500">Requested Amount</dt>
                        <dd className="mt-1 text-sm text-gray-900">{extractedFields.requestedAmount}</dd>
                      </div>
                    )}
                  </dl>
                </div>
              )}

              {/* Agriculture */}
              {(extractedFields.landSize || extractedFields.cropName || extractedFields.season) && (
                <div className="mt-4">
                  <h4 className="text-md font-medium text-gray-900 mb-3">Land / Agriculture</h4>
                  <dl className="grid grid-cols-1 gap-x-4 gap-y-3 sm:grid-cols-2">
                    {extractedFields.landSize && (
                      <div>
                        <dt className="text-sm font-medium text-gray-500">Land Size</dt>
                        <dd className="mt-1 text-sm text-gray-900">{extractedFields.landSize}{extractedFields.landUnit ? ` ${extractedFields.landUnit}` : ''}</dd>
                      </div>
                    )}
                    {extractedFields.cropName && (
                      <div>
                        <dt className="text-sm font-medium text-gray-500">Crop Name</dt>
                        <dd className="mt-1 text-sm text-gray-900">{extractedFields.cropName}</dd>
                      </div>
                    )}
                    {extractedFields.season && (
                      <div>
                        <dt className="text-sm font-medium text-gray-500">Season</dt>
                        <dd className="mt-1 text-sm text-gray-900">{extractedFields.season}</dd>
                      </div>
                    )}
                  </dl>
                </div>
              )}

              {/* Additional dynamic fields */}
              {Object.entries(extractedFields).filter(([k]) => ![
                'farmerName','guardianName','aadhaarNumber','mobileNumber','address','village','district','state',
                'annualIncome','requestedAmount','landSize','landUnit','surveyNumber','cropName','season'
              ].includes(k)).length > 0 && (
                <div className="mt-4">
                  <h4 className="text-md font-medium text-gray-900 mb-3">Additional Information</h4>
                  <dl className="grid grid-cols-1 gap-x-4 gap-y-3 sm:grid-cols-2">
                    {Object.entries(extractedFields).map(([key, value]) => {
                      if (!value) return null
                      if ([ 'farmerName','guardianName','aadhaarNumber','mobileNumber','address','village','district','state',
                        'annualIncome','requestedAmount','landSize','landUnit','surveyNumber','cropName','season'].includes(key)) return null
                      return (
                        <div key={key}>
                          <dt className="text-sm font-medium text-gray-500">{humanizeKey(key)}</dt>
                          <dd className="mt-1 text-sm text-gray-900">{String(value)}</dd>
                        </div>
                      )
                    })}
                  </dl>
                </div>
              )}

            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-gray-500">No extracted fields available yet</p>
              {application.aiProcessingStatus === 'processing' && (
                <p className="text-sm text-gray-400 mt-2">AI processing is in progress...</p>
              )}
              {application.aiProcessingStatus === 'failed' && (
                <p className="text-sm text-red-400 mt-2">AI processing failed. Please try reprocessing.</p>
              )}
            </div>
          )}
        </div>
      </SectionCard>

      {/* 3. Decision Support */}
      {hasDecisionSupport && (
        <SectionCard title={<div className="flex items-center justify-between w-full"><span className="font-semibold">Decision Support</span></div>}>
          <div className="p-4 bg-white rounded-lg border">
            <div className="flex items-center gap-3">
              <span className={`inline-flex px-3 py-1 text-xs font-semibold rounded-full ${normalizedData.decisionSupport.decision === 'approve' ? 'bg-green-100 text-green-800' : normalizedData.decisionSupport.decision === 'reject' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'}`}>
                {String(normalizedData.decisionSupport.decision || 'REVIEW').toUpperCase()}
              </span>
              {normalizedData.decisionSupport.confidence !== undefined && (
                <span className="text-sm text-gray-600">Confidence: {Math.round((normalizedData.decisionSupport.confidence || 0) * 100)}%</span>
              )}
            </div>
            {normalizedData.decisionSupport.reasoning && (
              <div className="mt-3 text-sm text-gray-800">
                {Array.isArray(normalizedData.decisionSupport.reasoning) ? (
                  <ul className="list-disc pl-5 space-y-1">
                    {normalizedData.decisionSupport.reasoning.map((r: string, i: number) => <li key={i}>{r}</li>)}
                  </ul>
                ) : (
                  <p>{normalizedData.decisionSupport.reasoning}</p>
                )}
              </div>
            )}
          </div>
        </SectionCard>
      )}

      {/* 4. Risk / Missing Fields */}
      {(hasRiskFlags || missingFields.length > 0) && (
        <SectionCard title={<div className="flex items-center justify-between w-full"><span className="font-semibold">Risk & Missing Fields</span></div>}>
          <div className="space-y-3">
            {hasRiskFlags && (
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-2">Risk Flags</h4>
                <div className="flex flex-wrap gap-2">
                  {(normalizedData.riskFlags || []).map((flag: any, idx: number) => (
                    <span key={idx} className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">{flag.message || flag.code || String(flag)}</span>
                  ))}
                </div>
              </div>
            )}

            {missingFields.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-2">Missing Fields</h4>
                <div className="flex flex-wrap gap-2">
                  {missingFields.map((mf: string, i: number) => (
                    <span key={i} className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">{humanizeKey(mf)}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </SectionCard>
      )}

      {/* 5. ML Insights */}
      {hasMlInsights && (
        <SectionCard title={
          <div onClick={() => setMlInsightsOpen(!mlInsightsOpen)} className="cursor-pointer flex items-center justify-between w-full">
            <span className="font-semibold">ML Insights</span>
            {mlInsightsOpen ? <ChevronDownIcon className="h-5 w-5 text-gray-400" /> : <ChevronRightIcon className="h-5 w-5 text-gray-400" />}
          </div>
        }>
          {mlInsightsOpen && (
            <div className="space-y-3">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="p-3 bg-white rounded-lg border text-center">
                  <div className="text-lg font-bold">{normalizePriorityScore(normalizedData.mlInsights.priority_score || 0)}%</div>
                  <div className="text-sm text-gray-600">Priority Score</div>
                </div>
                <div className="p-3 bg-white rounded-lg border text-center">
                  <div className="text-lg font-bold">{String((normalizedData.mlInsights.queue || '').replace('_',' ').toUpperCase() || 'NORMAL')}</div>
                  <div className="text-sm text-gray-600">Queue</div>
                </div>
                <div className="p-3 bg-white rounded-lg border text-center">
                  <div className="text-lg font-bold">{String((normalizedData.mlInsights.risk_level || '').toUpperCase() || 'MEDIUM')}</div>
                  <div className="text-sm text-gray-600">Risk Level</div>
                </div>
              </div>
            </div>
          )}
        </SectionCard>
      )}

      {/* Documents */}
      {application.documents && application.documents.length > 0 && (
        <SectionCard title="Uploaded Documents">
          <div className="space-y-3">
            {application.documents.map((doc: any, idx: number) => (
              <div key={idx} className="flex items-center justify-between p-3 border rounded-lg">
                <div>
                  <div className="font-medium text-gray-900">{doc.name}</div>
                  <div className="text-sm text-gray-500">{doc.type} • {doc.size ? `${(doc.size/1024/1024).toFixed(2)} MB` : 'Unknown size'}</div>
                </div>
                <div className="flex items-center space-x-2">
                  <StatusBadge status={doc.status || 'uploaded'} />
                  {doc.url && (
                    <button onClick={() => handleViewDocument(doc)} disabled={loadingFileUrl} className="text-blue-600 hover:text-blue-900 text-sm disabled:opacity-50 disabled:cursor-not-allowed">
                      {loadingFileUrl ? 'Loading...' : 'View'}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </SectionCard>
      )}

    </div>
  )
}
