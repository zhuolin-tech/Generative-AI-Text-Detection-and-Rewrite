# Generative AI Text Detection and Rewrite

A powerful AI-driven system for text detection and intelligent rewriting, featuring advanced natural language processing capabilities and a modular architecture.

## Features

### Text Detection
- AI-powered text analysis for detecting machine-generated content
- Real-time detection with detailed analysis reports
- Support for multiple text formats (raw text, PDF, DOC, DOCX, TXT)
- Sensitive content filtering with comprehensive word list

### Intelligent Rewriting
- Three rewriting modes: Easy, Medium, and Aggressive
- Chunk-based text processing for targeted rewriting
- Maintains readability while ensuring originality
- University-level content quality assurance

### User Management
- Comprehensive user account system
- Credit-based usage tracking
- Detailed usage history and analytics
- Referral system with reward mechanisms

### Payment Integration
- Multiple payment gateway support (Stripe, Airwallex)
- Flexible currency options (USD, RMB)
- Secure transaction processing
- Automated balance management

## Technical Architecture

### Backend Components
- **Routes Layer**: API endpoint management and request routing
- **Services Layer**: Core business logic and process handling
- **Forms Layer**: Data validation and database interactions
- **External API Layer**: Third-party service integration

### Key Modules
- `DocumentProcess`: Handles text processing and AI operations
- `MainService`: Manages core business operations
- `UserForm`: Handles user-related database operations
- `InputProcessing`: Text preprocessing and validation

## Innovation Highlights

1. **Advanced Text Processing**
   - Intelligent chunk-based processing
   - Context-aware rewriting
   - Multiple rewriting strength options

2. **Robust Security**
   - Comprehensive sensitive content filtering
   - Secure payment processing
   - Protected API endpoints

3. **Flexible Integration**
   - Multiple payment gateway support
   - Extensible API architecture
   - Modular component design

## API Usage

### Text Rewriting
```python
POST /humanize
Body: {
    "user_id": "string",
    "origin_text": "string",
    "mode": "medium"  # Options: easy, medium, aggressive
}
```

### Text Detection
```python
POST /check
Body: {
    "user_id": "string",
    "origin_text": "string"
}
```

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure environment variables
4. Start the application:
   ```bash
   python app.py
   ```

## Environment Variables

```env
MONGO_DB_CLOUD=<mongodb_connection_string>
STRIPE_PAY=<stripe_api_key>
AIRWALLEX_CLIENT_ID=<airwallex_client_id>
AIRWALLEX_API_KEY=<airwallex_api_key>
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
