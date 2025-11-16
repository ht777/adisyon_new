# Restaurant Ordering System

A comprehensive restaurant ordering system with real-time notifications, QR code table management, and multi-role authentication.

## 🚀 Features

- **Customer Interface**: Mobile-optimized web interface with QR code scanning
- **Admin Panel**: Complete management system for products, categories, tables, and orders
- **Kitchen Panel**: Real-time order display with status management and audio notifications
- **Multi-Role Authentication**: Admin, Kitchen, Waiter, and Supervisor roles
- **Real-time Communication**: WebSocket integration for instant order notifications
- **QR Code System**: Automatic QR code generation for each table
- **Responsive Design**: Works perfectly on mobile, tablet, and desktop devices
- **File Upload**: Product image upload with size validation
- **Analytics Dashboard**: Sales reports and statistics

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python) with SQLAlchemy ORM
- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Tailwind CSS
- **Database**: SQLite (development) / PostgreSQL (production)
- **Real-time**: WebSocket with automatic reconnection
- **Authentication**: JWT tokens with role-based access control
- **Deployment**: Docker with Nginx reverse proxy

## 📦 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- OpenSSL (for SSL certificate generation)

### Production Deployment

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd restaurant-ordering-system
   ```

2. **Generate SSL certificates** (for HTTPS)
   ```bash
   # Linux/Mac
   chmod +x generate-ssl.sh
   ./generate-ssl.sh
   
   # Windows
   generate-ssl.bat
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

4. **Deploy with Docker**
   ```bash
   # Linux/Mac
   chmod +x deploy.sh
   ./deploy.sh
   
   # Windows
   deploy.bat
   ```

5. **Access the application**
   - Customer Menu: https://localhost/menu
   - Admin Panel: https://localhost/admin
   - Kitchen Panel: https://localhost/kitchen
   - API Documentation: https://localhost/docs

### Local Development

1. **Install dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env file for development
   ```

3. **Run the application**
   ```bash
   # Start backend
   python main.py
   
   # Or use the start scripts
   # Windows: start.bat
   # Linux/Mac: start.sh
   ```

4. **Access the application**
   - Customer Menu: http://localhost:8000/menu
   - Admin Panel: http://localhost:8000/admin
   - Kitchen Panel: http://localhost:8000/kitchen
   - API Documentation: http://localhost:8000/docs

## 🔐 Default Credentials

The system creates default admin credentials on first startup:

- **Username**: admin
- **Password**: admin123

⚠️ **IMPORTANT**: Change the default password immediately after first login!

## 📱 Usage

### Customer Experience
1. Scan QR code at the table
2. Browse the digital menu
3. Add items to cart with customizations
4. Place order with real-time status updates
5. Receive notifications when order is ready

### Admin Management
1. Login to admin panel
2. Manage categories and products
3. Configure tables and generate QR codes
4. Monitor orders and sales analytics
5. Manage user accounts and permissions

### Kitchen Operations
1. Kitchen staff login to kitchen panel
2. View incoming orders in real-time
3. Update order status (preparing, ready, delivered)
4. Receive audio notifications for new orders
5. Track order completion times

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./restaurant.db` |
| `SECRET_KEY` | JWT secret key | Random string |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000` |
| `DEBUG` | Debug mode | `false` |
| `ENVIRONMENT` | Environment type | `development` |
| `UPLOAD_DIR` | File upload directory | `frontend/static/uploads` |
| `MAX_FILE_SIZE_MB` | Maximum file upload size | `5` |

### Docker Configuration

The system includes:
- **PostgreSQL** database container
- **Redis** cache container (optional)
- **Backend** API container
- **Nginx** reverse proxy container

### SSL Configuration

For production deployment:
1. Replace self-signed certificates with valid SSL certificates
2. Update `nginx.conf` with your domain configuration
3. Configure proper DNS records

## 🚀 Deployment Options

### Docker Compose (Recommended)
```bash
docker-compose up -d
```

### Manual Deployment
1. Set up PostgreSQL database
2. Configure Nginx reverse proxy
3. Deploy backend application
4. Configure SSL certificates

### Cloud Deployment
- **AWS ECS**: Use provided Docker configuration
- **Google Cloud Run**: Container-based deployment
- **Azure Container Instances**: Managed container service

## 📊 API Documentation

Interactive API documentation is available at:
- Swagger UI: `/docs`
- ReDoc: `/redoc`

### Key Endpoints

- `POST /api/auth/login` - User authentication
- `GET /api/products` - List products
- `POST /api/orders` - Create order
- `GET /api/tables/{id}/qr` - Generate table QR code
- `WS /ws` - WebSocket connection

## 🔒 Security Features

- JWT-based authentication
- Role-based access control
- Input validation and sanitization
- CORS protection
- Rate limiting
- SQL injection prevention
- XSS protection

## 📈 Monitoring

Health check endpoint: `/health`
- Database connectivity
- WebSocket status
- System information
- Connection statistics

## 🛠️ Development

### Project Structure
```
restaurant-ordering-system/
├── backend/
│   ├── routers/          # API endpoints
│   ├── models.py         # Database models
│   ├── auth.py           # Authentication
│   └── main.py           # Application entry
├── frontend/
│   └── static/           # HTML, CSS, JS files
├── docker-compose.yml    # Docker orchestration
├── nginx.conf           # Nginx configuration
└── deploy.sh            # Deployment script
```

### Adding New Features
1. Create database models in `models.py`
2. Add API endpoints in `routers/`
3. Update frontend interfaces
4. Add WebSocket notifications if needed
5. Update documentation

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check database service status
   - Verify connection string in `.env`
   - Ensure database is initialized

2. **WebSocket Connection Issues**
   - Check firewall settings
   - Verify Nginx configuration
   - Enable WebSocket support in proxy

3. **File Upload Problems**
   - Check upload directory permissions
   - Verify file size limits
   - Ensure proper file extensions

4. **SSL Certificate Errors**
   - Regenerate certificates if needed
   - Check certificate file paths
   - Verify Nginx SSL configuration

### Logs and Debugging

```bash
# View container logs
docker-compose logs -f

# View specific service logs
docker-compose logs backend
docker-compose logs nginx

# Check system health
curl -f https://localhost/health
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Check the documentation
- Review troubleshooting section
- Create an issue in the repository

## 🔄 Updates

To update the system:
1. Pull latest changes
2. Rebuild containers: `docker-compose build --no-cache`
3. Restart services: `docker-compose up -d`
4. Check health endpoint: `/health`

---

**⭐ Star this repository if you find it helpful!**