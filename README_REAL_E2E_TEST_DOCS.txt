REAL E2E TEST DOCUMENTS FOR AGRI ADMIN SYSTEM

Purpose:
These PDFs are meant for truthful end-to-end testing of:
- upload
- AI processing
- classification
- extraction
- ML insights
- workflow
- duplicate / re-upload behavior

Recommended usage:
1. Use these files from disk in test_real_document_e2e.py
2. Upload each file once with a unique applicant/test user
3. Poll application detail until aiProcessingStatus == completed
4. Validate extractedData, aiSummary, ml_insights, workflow
5. For duplicate test:
   - upload the same file again before completion -> expect 409 duplicate_blocked
6. For re-upload test:
   - approve original completed application
   - upload same file again -> expect reupload_allowed and incremented version

Included files:
- 01_scheme_application_pm_kisan.pdf
- 02_subsidy_claim_drip_irrigation.pdf
- 03_insurance_claim_crop_loss.pdf
- 04_grievance_delayed_subsidy_payment.pdf
- 05_farmer_record_profile.pdf
- 06_supporting_document_land_receipt.pdf

Also included:
- expected_manifest.json
- expected_manifest.csv
