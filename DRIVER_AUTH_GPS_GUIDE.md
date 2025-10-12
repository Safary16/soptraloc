# Driver Authentication & GPS Tracking System

## Overview

This document describes the implementation of the driver authentication and GPS tracking system for SoptraLoc TMS.

## Features Implemented

### 1. User Authentication for Drivers

Each driver now has a dedicated user account for secure access to their dashboard.

**Key Components:**
- `Driver.user` field: OneToOne relationship with Django's User model
- Login page at `/driver/login/`
- Logout functionality at `/driver/logout/`
- Protected driver dashboard requiring authentication

**Admin Interface:**
- When creating/editing a driver in admin, users can be auto-created
- Default password format: `driver123` (should be changed on first login)
- Username generated from driver name (e.g., "Juan Pérez" → "juan_pérez")

### 2. GPS Tracking System

Real-time GPS tracking of drivers with historical data storage.

**Models:**
- `DriverLocation`: Stores GPS tracking history with timestamp, accuracy
- `Driver.ultima_posicion_lat/lng`: Current location for quick access

**API Endpoints:**
- `POST /api/drivers/{id}/track_location/`: Record GPS position
  - Requires authentication
  - Driver can only update their own location
  - Stores in both Driver model and DriverLocation history

- `GET /api/drivers/active_locations/`: Get all active drivers' positions
  - Returns drivers with location updated in last 30 minutes
  - Includes assigned container and destination CD information
  - Used by monitoring page

- `GET /api/drivers/{id}/my_info/`: Get authenticated driver's info
  - Returns driver details and assigned programaciones
  - Includes container, CD address, and pickup location

### 3. Driver Dashboard

Enhanced mobile-friendly dashboard for drivers (`/driver/dashboard/`)

**Features:**
- **Authentication Required**: Must login to access
- **GPS Permission Request**: Automatically requests location access on load
- **Continuous Tracking**: Uses `watchPosition` to track location every 30 seconds
- **Notification Permission**: Requests permission to receive push notifications
- **Assignment Display**: Shows assigned containers with:
  - Container number and client
  - Destination CD name and address
  - Pickup location for the driver
  - ETA and distance
  - Direct link to Google Maps for navigation

**GPS Tracking Flow:**
1. Page loads → Request location permission
2. User grants permission → Get initial position
3. Send position to server via `track_location` API
4. Start continuous tracking with `watchPosition`
5. Update server every 30 seconds automatically

### 4. Real-Time Monitoring Page

Admin/operations view to monitor all active drivers (`/monitoring/`)

**Features:**
- **Live Map**: Mapbox GL JS integration showing driver positions
- **Auto-Refresh**: Updates every 15 seconds
- **Driver List**: Sidebar with active drivers and their status
- **Route Visualization**: Shows estimated route from driver to destination
- **Interactive Markers**: Click driver on map or list to focus
- **Status Indicators**: Shows last update time and ETA

**Map Features:**
- Driver markers with popup showing details
- Dashed line from driver to destination CD
- Auto-fit bounds to show all drivers
- Navigation controls and fullscreen mode

### 5. Notifications

Automated notifications when drivers are assigned containers.

**Implementation:**
- Notification created in `Programacion.asignar_conductor()`
- Includes container number, CD name, address, and schedule
- Web notification permission requested in driver dashboard
- Shows welcome notification when permission granted

## Usage Guide

### For Administrators

**Creating Driver Users:**

1. Go to Django Admin → Drivers
2. Create or edit a driver
3. Leave the "User" field blank - it will auto-create on save
4. Note the generated username and password from the success message
5. Share credentials with the driver

**Monitoring Drivers:**

1. Navigate to `/monitoring/`
2. View real-time positions on map
3. See driver status, assigned containers, and ETAs
4. Auto-refreshes every 15 seconds

### For Drivers

**First Login:**

1. Navigate to `/driver/login/`
2. Enter username and password provided by admin
3. Grant GPS location permission when prompted
4. Grant notification permission when prompted

**Using Dashboard:**

1. View assigned containers in "Mis Entregas" section
2. Each container shows:
   - Container number and client name
   - Where to pick up the container (CD address)
   - Destination information
   - Button to open Google Maps for directions
3. GPS automatically tracks your position
4. Receive notifications when assigned new containers

**GPS Tracking:**

- Runs automatically in background
- Updates every 30 seconds while dashboard is open
- Shows accuracy in header (e.g., "±10m")
- No manual action needed

## API Reference

### Authentication

All driver-specific endpoints require authentication via session or JWT token.

### Endpoints

#### `POST /api/drivers/{id}/track_location/`

Record driver's GPS position.

**Request:**
```json
{
  "lat": -33.4489,
  "lng": -70.6693,
  "accuracy": 10.5
}
```

**Response:**
```json
{
  "success": true,
  "mensaje": "Ubicación registrada",
  "location": {
    "id": 123,
    "driver": 1,
    "driver_name": "Juan Pérez",
    "lat": "-33.448900",
    "lng": "-70.669300",
    "accuracy": 10.5,
    "timestamp": "2025-10-12T16:30:00Z"
  }
}
```

#### `GET /api/drivers/active_locations/`

Get all active drivers with recent GPS updates.

**Response:**
```json
{
  "success": true,
  "total": 2,
  "drivers": [
    {
      "id": 1,
      "nombre": "Juan Pérez",
      "lat": -33.4489,
      "lng": -70.6693,
      "ultima_actualizacion": "2025-10-12T16:30:00Z",
      "telefono": "+56912345678",
      "container": "ABCD1234567",
      "cd_destino": "CD Maipú",
      "cd_lat": -33.5,
      "cd_lng": -70.7,
      "eta_minutos": 25
    }
  ]
}
```

#### `GET /api/drivers/{id}/my_info/`

Get authenticated driver's information and assignments.

**Response:**
```json
{
  "success": true,
  "driver": {
    "id": 1,
    "nombre": "Juan Pérez",
    "presente": true,
    "activo": true,
    "num_entregas_dia": 1,
    "max_entregas_dia": 3
  },
  "programaciones": [
    {
      "id": 10,
      "container": {
        "numero": "ABCD1234567",
        "tipo": "20HC",
        "estado": "asignado"
      },
      "cd": {
        "nombre": "CD Maipú",
        "direccion": "Av. Pajaritos 3000, Maipú",
        "lat": -33.5,
        "lng": -70.7,
        "telefono": "+56221234567",
        "horario": "8:00 - 18:00"
      },
      "fecha_programada": "2025-10-12T09:00:00Z",
      "cliente": "Cliente SA",
      "direccion_entrega": "Dirección final",
      "observaciones": "Entregar antes de las 15:00",
      "eta_minutos": 25,
      "distancia_km": 15.5
    }
  ]
}
```

## Database Schema

### Driver Model Changes

```python
class Driver(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    # ... existing fields ...
```

### New Model: DriverLocation

```python
class DriverLocation(models.Model):
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='location_history')
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    lng = models.DecimalField(max_digits=9, decimal_places=6)
    accuracy = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
```

## Testing

Comprehensive test suite included in `apps/drivers/tests.py`:

**Test Coverage:**
- Driver authentication (login/logout)
- Dashboard access control
- GPS tracking API
- Location history
- Permission enforcement

**Run Tests:**
```bash
python manage.py test apps.drivers.tests
```

All 12 tests pass successfully.

## Security Considerations

1. **Authentication Required**: All driver-specific endpoints require authentication
2. **Permission Checks**: Drivers can only access their own data
3. **HTTPS Recommended**: GPS and notification permissions require secure context
4. **Password Security**: Default passwords should be changed on first login
5. **Location Privacy**: Historical location data stored securely

## Browser Compatibility

**GPS Tracking:**
- Chrome/Edge: Full support
- Firefox: Full support
- Safari: Full support (iOS requires HTTPS)
- Opera: Full support

**Notifications:**
- Chrome/Edge: Full support
- Firefox: Full support
- Safari: Limited (iOS doesn't support Web Push)

## Future Enhancements

- [ ] Push notification backend (FCM/OneSignal integration)
- [ ] Offline mode for GPS tracking
- [ ] Route optimization suggestions
- [ ] Driver performance metrics dashboard
- [ ] Export GPS tracking data
- [ ] Geofencing alerts

## Troubleshooting

**GPS Not Working:**
1. Check browser permissions (chrome://settings/content/location)
2. Ensure HTTPS is used (HTTP only works on localhost)
3. Check console for errors
4. Verify device has GPS enabled

**Login Issues:**
1. Verify user has driver_profile relationship
2. Check username/password are correct
3. Ensure driver.user is not null

**Monitoring Page Not Updating:**
1. Check MAPBOX_API_KEY is configured
2. Verify drivers have recent location updates (< 30 min)
3. Check browser console for API errors

## Configuration

### Environment Variables

```env
# Mapbox API key for monitoring page
MAPBOX_API_KEY=pk.your_mapbox_token_here
```

### Settings

```python
# In config/settings.py
MAPBOX_API_KEY = config('MAPBOX_API_KEY', default=None)
```
