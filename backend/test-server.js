const express = require('express');
const multer = require('multer');
const cors = require('cors');
const { PrismaClient } = require('./generated/prisma');
const { createClient } = require('@supabase/supabase-js');

// Initialize Supabase client
const supabase = createClient(
  process.env.SUPABASE_URL || 'https://your-project.supabase.co',
  process.env.SUPABASE_ANON_KEY || 'your-anon-key'
);

const app = express();
const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 10 * 1024 * 1024 },
  fileFilter: (req, file, cb) => {
    if (file.mimetype.startsWith('image/') || file.mimetype === 'application/pdf') {
      cb(null, true);
    } else {
      cb(new Error('Only image and PDF files are allowed'));
    }
  },
});

// CORS
app.use(cors({
  origin: ['http://localhost:3000', 'http://localhost:3002'],
  credentials: true
}));

// Body parsing
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Basic health check
app.get('/health', (req, res) => {
  res.json({ status: 'OK', service: 'Test Backend' });
});

// Simple upload endpoint with Supabase storage
app.post('/api/applications/upload', upload.single('file'), async (req, res) => {
  console.log('[UPLOAD] File received:', !!req.file);
  
  if (!req.file) {
    return res.status(400).json({ error: 'No file uploaded' });
  }

  try {
    // Upload file to Supabase storage
    const bucket = 'documents'
    const objectPath = `applications/${Date.now()}-${req.file.originalname}`
    console.log('[UPLOAD] Starting Supabase storage upload:', { bucket, objectPath });

    const { data: uploadData, error: uploadError } = await supabase.storage
      .from(bucket)
      .upload(objectPath, req.file.buffer, {
        contentType: req.file.mimetype,
        upsert: false
      })

    if (uploadError) {
      console.error('[UPLOAD] Supabase storage upload failed:', uploadError);
      return res.status(500).json({ 
        error: 'File upload failed', 
        details: uploadError.message 
      })
    }

    console.log('[UPLOAD] Supabase storage upload successful:', uploadData.path);

    // Mock database save with real Supabase object path
    const application = {
      id: `test-${Date.now()}`,
      status: 'uploaded',
      aiProcessingStatus: 'processing',
      fileName: req.file.originalname,
      fileSize: req.file.size,
      fileType: req.file.mimetype,
      fileUrl: uploadData.path, // Store Supabase object path instead of local-files
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };

    console.log('[UPLOAD] Application created:', application.id);

    // Trigger AI processing asynchronously
    setTimeout(async () => {
      console.log('[AI] Processing started for:', application.id);
      
      // Mock AI processing result
      const mockExtractedData = {
        farmer_name: 'Rajesh Kumar Singh',
        aadhaar_number: '1234-5678-9012',
        land_size: '5.2 acres',
        annual_income: '45000',
        scheme_name: 'PM-KISAN',
        location: 'Rampur, Pune',
        extractionConfidence: 0.85,
        missingFields: [],
        extractedAt: new Date().toISOString()
      };

      // In a real implementation, this would update the database
      console.log('[AI] Processing completed for:', application.id);
      console.log('[AI] Extracted data:', mockExtractedData);
    }, 3000);

    res.status(201).json(application);
  } catch (error) {
    console.error('[UPLOAD] Error:', error);
    res.status(500).json({ error: 'Upload failed' });
  }
});

// Get application details
app.get('/api/applications/:id', async (req, res) => {
  const { id } = req.params;
  
  // Mock application with AI processed data
  const application = {
    id,
    status: 'processed',
    aiProcessingStatus: 'completed',
    extractedData: {
      farmer_name: 'Rajesh Kumar Singh',
      aadhaar_number: '1234-5678-9012',
      land_size: '5.2 acres',
      annual_income: '45000',
      scheme_name: 'PM-KISAN',
      location: 'Rampur, Pune',
      extractionConfidence: 0.85,
      missingFields: [],
      extractedAt: new Date().toISOString()
    },
    aiSummary: 'Application complete with all required fields',
    priorityScore: 75,
    fraudRiskScore: 0.1,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  };

  res.json(application);
});

const PORT = 3001;
app.listen(PORT, () => {
  console.log(`Test backend running on port ${PORT}`);
});
