# 🚀 Driver Authentication & GPS Tracking System - Implementation Guide

## 📋 Overview

Complete implementation of driver authentication and GPS tracking system for SoptraLoc TMS. This system allows administrators to create individual user accounts for drivers, enables secure driver login, tracks GPS location in real-time, and provides a monitoring dashboard.

## ✨ Key Features

### 1. Driver Authentication
- **Individual user accounts** for each driver
- **Secure login** with username/password
- **Auto-user creation** in Django Admin
- **Session-based authentication**

### 2. GPS Tracking
- **Real-time location tracking** from driver's smartphone
- **Historical GPS data** storage with timestamps
- **Continuous tracking** every 30 seconds
- **Accuracy tracking** (meters)

### 3. Real-Time Monitoring
- **Live map** with Mapbox integration
- **Active driver visualization** with markers
- **Auto-refresh** every 15 seconds
- **Driver status indicators** with pulse animation

### 4. Driver Dashboard
- **Mobile-optimized** interface
- **Automatic GPS permission** request
- **Assigned deliveries** display
- **Pickup location** information with Google Maps navigation

## 🎯 Quick Start

### For Administrators

#### 1. Create a Driver with User Account

```bash
# Navigate to Django Admin
http://yourdomain.com/admin/

# Go to Drivers section
# Click "Add Driver"
# Fill in driver information:
#   - Name: Juan Pérez
#   - RUT: 12345678-9
#   - Phone: +56912345678
# Leave 'user' field BLANK
# Click "Save"

# System automatically creates user:
# ✓ Username: juan_perez
# ✓ Password: driver123
# (Credentials shown in success message)
```

#### 2. View Real-Time Monitoring

```bash
# Navigate to monitoring page
http://yourdomain.com/monitoring/

# Features:
# - Live map with driver positions
# - Sidebar with driver list
# - Auto-refresh every 15 seconds
# - Click driver to focus on map
```

### For Drivers

#### 1. Login to Dashboard

```bash
# Navigate to driver login
http://yourdomain.com/driver/login/

# Enter credentials provided by admin
Username: juan_perez
Password: driver123

# Click "Iniciar Sesión"
```

#### 2. Use Dashboard

Once logged in, the dashboard will:
- ✅ Request GPS permission (allow when prompted)
- ✅ Request notification permission
- ✅ Start continuous GPS tracking
- ✅ Display assigned containers
- ✅ Show pickup locations with directions

## 🔧 API Reference

### Authentication Endpoints

#### Driver Login Page
```http
GET /driver/login/
```
Returns the login page with beautiful gradient design.

#### Process Login
```http
POST /driver/login/
Content-Type: application/x-www-form-urlencoded

username=juan_perez&password=driver123
```

#### Driver Dashboard
```http
GET /driver/dashboard/
Authorization: Session (requires login)
```

#### Logout
```http
GET /driver/logout/
```

### GPS Tracking Endpoints

#### Record GPS Position
```http
POST /api/drivers/{id}/track_location/
Content-Type: application/json
Authorization: Session (must be authenticated as that driver)

{
  "lat": -33.4569,
  "lng": -70.6483,
  "accuracy": 10.5
}
```

**Response:**
```json
{
  "success": true,
  "mensaje": "Ubicación actualizada",
  "lat": -33.4569,
  "lng": -70.6483,
  "timestamp": "2025-10-12T15:30:00Z"
}
```

#### Get Active Driver Locations
```http
GET /api/drivers/active_locations/
```

Returns all drivers with GPS data from the last 30 minutes.

**Response:**
```json
[
  {
    "id": 1,
    "nombre": "Juan Pérez",
    "lat": -33.4569,
    "lng": -70.6483,
    "ultima_actualizacion": "2025-10-12T15:30:00Z",
    "num_entregas_dia": 2,
    "max_entregas_dia": 5
  }
]
```

#### Get Driver Info with Assignments
```http
GET /api/drivers/{id}/my_info/
Authorization: Session (must be authenticated as that driver)
```

**Response:**
```json
{
  "id": 1,
  "nombre": "Juan Pérez",
  "programaciones_asignadas": [
    {
      "id": 1,
      "contenedor": "ABCD1234567",
      "cliente": "Walmart",
      "cd": "CCTI",
      "cd_direccion": "Av. Pedro Fontova 6951, Pudahuel",
      "cd_telefono": "+56222334455",
      "cd_horario": "08:00 - 18:00",
      "estado": "asignado"
    }
  ]
}
```

#### Get Location History
```http
GET /api/drivers/{id}/historial/?dias=7
```

Returns GPS history for the last N days (default: 7).

### Management Endpoints

#### List All Drivers
```http
GET /api/drivers/
```

Optional filters:
- `?activo=true` - Only active drivers
- `?presente=true` - Only present drivers

#### Reset Daily Deliveries
```http
POST /api/drivers/{id}/reset_entregas_diarias/
```

## 📊 Database Schema

### Driver Model

```python
class Driver(models.Model):
    # Authentication
    user = models.OneToOneField(User, null=True, blank=True)
    
    # Basic Info
    nombre = models.CharField(max_length=200)
    rut = models.CharField(max_length=20, unique=True)
    telefono = models.CharField(max_length=20)
    
    # Availability
    presente = models.BooleanField(default=True)
    activo = models.BooleanField(default=True)
    
    # Performance
    cumplimiento_porcentaje = models.DecimalField(max_digits=5, decimal_places=2)
    num_entregas_dia = models.IntegerField(default=0)
    max_entregas_dia = models.IntegerField(default=3)
    
    # GPS Position
    ultima_posicion_lat = models.DecimalField(max_digits=9, decimal_places=6)
    ultima_posicion_lng = models.DecimalField(max_digits=9, decimal_places=6)
    ultima_actualizacion_posicion = models.DateTimeField()
    
    # Stats
    total_entregas = models.IntegerField(default=0)
    entregas_a_tiempo = models.IntegerField(default=0)
```

### DriverLocation Model

```python
class DriverLocation(models.Model):
    driver = models.ForeignKey(Driver, related_name='ubicaciones')
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    lng = models.DecimalField(max_digits=9, decimal_places=6)
    accuracy = models.FloatField(null=True)  # meters
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
```

## 🧪 Testing

Run the test suite:

```bash
python manage.py test apps.drivers
```

**Test Coverage:**
- ✅ Driver authentication flow (login/logout)
- ✅ Dashboard access control
- ✅ GPS tracking API endpoints
- ✅ Location history storage
- ✅ Permission enforcement
- ✅ Model methods and properties
- ✅ Driver availability calculation

**Results:** 17 tests, all passing ✓

## 🔐 Security Features

1. **Session-based authentication** - Secure cookie-based sessions
2. **CSRF protection** - All forms protected against CSRF attacks
3. **Permission checks** - Drivers can only update their own location
4. **Secure passwords** - Django's built-in password hashing (PBKDF2)
5. **Protected routes** - Dashboard requires authentication
6. **HTTPS required** - GPS/notifications require HTTPS in production

## 🎨 UI/UX Features

### Login Page
- Purple-to-violet gradient background
- Centered card with shadow
- Font Awesome icons
- Responsive mobile design
- Error message display

### Driver Dashboard
- Mobile-optimized layout
- GPS accuracy indicator
- Delivery cards with CD information
- Google Maps navigation integration
- Floating logout button
- Auto-refresh display

### Monitoring Page
- Split-screen layout (sidebar + map)
- Mapbox integration
- Driver markers with popups
- Status indicators with pulse animation
- Auto-refresh every 15 seconds
- Click-to-focus functionality

## 📱 Browser Compatibility

### Desktop
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

### Mobile
- ✅ Chrome Mobile (Android)
- ✅ Safari iOS
- ✅ Samsung Internet

**Note:** GPS and notifications require HTTPS in production (localhost works without HTTPS for testing)

## 🚀 Deployment Checklist

- [ ] Set `DEBUG = False` in production
- [ ] Configure HTTPS certificate
- [ ] Set `SECURE_SSL_REDIRECT = True`
- [ ] Set `SESSION_COOKIE_SECURE = True`
- [ ] Set `CSRF_COOKIE_SECURE = True`
- [ ] Update `ALLOWED_HOSTS`
- [ ] Configure Mapbox API key
- [ ] Run migrations: `python manage.py migrate`
- [ ] Collect static files: `python manage.py collectstatic`
- [ ] Create superuser: `python manage.py createsuperuser`
- [ ] Test GPS on HTTPS domain
- [ ] Test notifications on HTTPS domain

## 📝 Configuration

### Required Settings

Add to `config/settings.py`:

```python
# Login URLs
LOGIN_URL = '/driver/login/'
LOGIN_REDIRECT_URL = '/driver/dashboard/'
LOGOUT_REDIRECT_URL = '/driver/login/'

# Mapbox (for monitoring page)
MAPBOX_API_KEY = config('MAPBOX_API_KEY', default=None)
```

### Environment Variables

Create `.env` file:

```bash
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=sqlite:///db.sqlite3

# Mapbox
MAPBOX_API_KEY=pk.your.mapbox.token
```

## 🎯 Future Enhancements

Potential improvements:

1. **Push Notifications**
   - Integration with FCM/OneSignal
   - Real-time alerts for new assignments

2. **Offline Support**
   - Service Worker for offline GPS tracking
   - Sync when connection restored

3. **Route Optimization**
   - Suggest optimal routes
   - Traffic-aware routing

4. **Analytics**
   - Driver performance reports
   - GPS tracking heatmaps
   - Delivery time analysis

5. **Geofencing**
   - Alerts when entering/leaving zones
   - Automatic check-in at locations

## 🐛 Troubleshooting

### GPS Not Working

**Problem:** GPS tracking not updating on driver dashboard

**Solutions:**
1. Check browser console for errors
2. Verify GPS permissions granted
3. Ensure HTTPS in production
4. Check network connectivity
5. Verify driver is authenticated

### Login Redirects to Wrong Page

**Problem:** After login, redirects to `/accounts/login/`

**Solution:**
Add to `settings.py`:
```python
LOGIN_URL = '/driver/login/'
```

### Monitoring Page Shows No Drivers

**Problem:** Monitoring page shows "No hay conductores activos"

**Possible Causes:**
1. No drivers with recent GPS data (last 30 minutes)
2. Driver not active (`activo=False`)
3. GPS tracking not running on driver's device

**Solution:**
1. Check driver has tracked location recently
2. Verify driver is `activo=True` in admin
3. Test GPS tracking with a driver

### Mapbox Not Loading

**Problem:** Map shows error or doesn't load

**Solutions:**
1. Verify Mapbox API key is valid
2. Check network connectivity
3. Verify Mapbox token has correct permissions
4. Check browser console for errors

## 📞 Support

For issues or questions:
1. Check this documentation
2. Review test cases in `apps/drivers/tests.py`
3. Check server logs for errors
4. Verify all migrations applied: `python manage.py showmigrations`

---

**Implementation Date:** October 2025  
**Version:** 1.0.0  
**Status:** ✅ Complete and Tested
