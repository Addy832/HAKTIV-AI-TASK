# HAKTIV AI - Compliance Management System

An AI-powered compliance validation and evidence management system built with Django and Next.js.

## 🚀 Features

- **AI-Powered Compliance Analysis**: Automatic validation of evidence using Google Gemini AI
- **Multi-Factor Authentication (MFA) Controls**: Validate OTP and authenticator screenshots
- **Single Sign-On (SSO) Controls**: Verify Microsoft Azure AD SSO implementations
- **Evidence Management**: Upload, store, and track compliance evidence
- **Real-time Status Updates**: Immediate feedback on compliance validation
- **Company-based Access Control**: Multi-tenant architecture with company isolation
- **Microsoft SSO Integration**: Seamless authentication with Azure AD

## 🏗️ Architecture

### Backend (Django)

- **API Endpoints**: RESTful API for evidence management and compliance checks
- **AI Integration**: Google Gemini API for image analysis
- **Database Models**: Evidence, Controls, Companies, Users, and Compliance Checks
- **Authentication**: Microsoft Azure AD OAuth2 integration
- **File Management**: Secure file upload and storage

### Frontend (Next.js)

- **Modern UI**: Responsive design with Tailwind CSS
- **Real-time Updates**: Automatic status refresh after uploads
- **File Upload**: Drag-and-drop evidence upload interface
- **Compliance Dashboard**: Visual status tracking and analysis results

## 🛠️ Technology Stack

- **Backend**: Django 5.2.6, PostgreSQL, Google Gemini AI
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **Authentication**: Microsoft Azure AD OAuth2
- **Deployment**: Docker, Docker Compose
- **AI/ML**: Google Gemini 2.0 Flash for image analysis

## 📋 Compliance Controls

### MFA Control - OTP Authentication

- Validates OTP input fields and 6-digit codes
- Detects authenticator app references
- Ensures proper labeling and QR codes

### SSO Login Control - Microsoft Azure AD

- Verifies Microsoft branding and logos
- Confirms "Sign in with Microsoft" buttons
- Validates Azure AD integration visibility

## 🚀 Quick Start

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd HAKTIV-AI-TASK
   ```

2. **Set up environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start with Docker**

   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Django Admin: http://localhost:8000/admin

## 🔧 Configuration

### Required Environment Variables

- `AI_API_KEY`: Google Gemini API key
- `AI_API_URL`: Gemini API endpoint
- `SOCIAL_AUTH_AZUREAD_OAUTH2_KEY`: Azure AD client ID
- `SOCIAL_AUTH_AZUREAD_OAUTH2_SECRET`: Azure AD client secret

### Database Setup

The system automatically:

- Runs database migrations
- Seeds default controls for all companies
- Creates admin users for each company

## 📊 API Endpoints

- `POST /api/evidence/upload/` - Upload evidence files
- `GET /api/evidence/` - List evidence records
- `GET /api/control/` - List compliance controls
- `GET /api/compliance/checks/` - Get compliance analysis results
- `POST /auth/login/azuread-oauth2/` - Microsoft SSO login

## 🎯 AI Analysis Features

- **Image Recognition**: Analyzes screenshots for compliance indicators
- **Confidence Scoring**: Provides confidence levels for analysis results
- **Detailed Feedback**: Explains reasoning and detected elements
- **Recommendations**: Suggests improvements for non-compliant evidence

## 🔒 Security Features

- **Company Isolation**: Users only see their company's data
- **Secure File Storage**: Protected evidence file access
- **OAuth2 Authentication**: Secure Microsoft SSO integration
- **Input Validation**: Comprehensive file and data validation

## 📱 User Experience

- **Intuitive Interface**: Clean, modern design
- **Real-time Feedback**: Immediate upload status and analysis results
- **Mobile Responsive**: Works seamlessly on all devices
- **Accessibility**: WCAG compliant interface design

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Google Gemini AI for powerful image analysis capabilities
- Microsoft Azure AD for secure authentication
- Django and Next.js communities for excellent frameworks
- Tailwind CSS for beautiful, responsive design
