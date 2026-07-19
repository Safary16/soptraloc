/**
 * SoptraLoc Driver - Native Android App
 * GPS Background Tracking habilitado incluso con pantalla bloqueada
 */

import React, {useEffect, useState} from 'react';
import {
  SafeAreaView,
  StyleSheet,
  Text,
  View,
  TextInput,
  TouchableOpacity,
  Alert,
  PermissionsAndroid,
  Platform,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import Geolocation from 'react-native-geolocation-service';
import BackgroundService from 'react-native-background-actions';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';

// Configuración del servidor backend
const API_BASE_URL = 'https://soptraloc.onrender.com';

const App = () => {
  const [patente, setPatente] = useState('');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [driverId, setDriverId] = useState(null);
  const [driverName, setDriverName] = useState('');
  const [isTracking, setIsTracking] = useState(false);
  const [loading, setLoading] = useState(false);
  const [lastLocation, setLastLocation] = useState(null);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  // Verificar si ya está autenticado
  const checkAuthStatus = async () => {
    try {
      const savedDriverId = await AsyncStorage.getItem('driverId');
      const savedDriverName = await AsyncStorage.getItem('driverName');
      const savedPatente = await AsyncStorage.getItem('patente');
      
      if (savedDriverId && savedDriverName) {
        setDriverId(savedDriverId);
        setDriverName(savedDriverName);
        setPatente(savedPatente || '');
        setIsAuthenticated(true);
        
        // Verificar si el tracking ya está activo
        const trackingActive = await BackgroundService.isRunning();
        setIsTracking(trackingActive);
      }
    } catch (error) {
      console.error('Error checking auth status:', error);
    }
  };

  // Solicitar permisos de ubicación
  const requestLocationPermission = async () => {
    if (Platform.OS === 'android') {
      try {
        const granted = await PermissionsAndroid.request(
          PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION,
          {
            title: 'Permiso de Ubicación',
            message:
              'SoptraLoc necesita acceso a tu ubicación para rastrear entregas',
            buttonNeutral: 'Preguntar Después',
            buttonNegative: 'Cancelar',
            buttonPositive: 'Permitir',
          },
        );
        
        // Solicitar permiso de ubicación en segundo plano (Android 10+)
        if (Platform.Version >= 29) {
          const bgGranted = await PermissionsAndroid.request(
            PermissionsAndroid.PERMISSIONS.ACCESS_BACKGROUND_LOCATION,
            {
              title: 'Permiso de Ubicación en Segundo Plano',
              message:
                'Permite que SoptraLoc acceda a tu ubicación incluso cuando la app está cerrada',
              buttonNeutral: 'Preguntar Después',
              buttonNegative: 'Cancelar',
              buttonPositive: 'Permitir Siempre',
            },
          );
          return (
            granted === PermissionsAndroid.RESULTS.GRANTED &&
            bgGranted === PermissionsAndroid.RESULTS.GRANTED
          );
        }
        
        return granted === PermissionsAndroid.RESULTS.GRANTED;
      } catch (err) {
        console.warn(err);
        return false;
      }
    }
    return true;
  };

  // Autenticar conductor con patente
  const handleLogin = async () => {
    if (!patente.trim()) {
      Alert.alert('Error', 'Por favor ingresa la patente del vehículo');
      return;
    }

    setLoading(true);
    try {
      // Verificar patente contra el backend
      const response = await axios.post(
        `${API_BASE_URL}/api/drivers/verify-patente/`,
        {patente: patente.trim().toUpperCase()},
      );

      if (response.data.success) {
        const {driver_id, driver_name} = response.data;
        
        // Guardar datos del conductor
        await AsyncStorage.setItem('driverId', driver_id.toString());
        await AsyncStorage.setItem('driverName', driver_name);
        await AsyncStorage.setItem('patente', patente.trim().toUpperCase());
        
        setDriverId(driver_id);
        setDriverName(driver_name);
        setIsAuthenticated(true);
        
        Alert.alert('Éxito', `Bienvenido ${driver_name}`);
      } else {
        Alert.alert('Error', 'Patente no válida o no asignada');
      }
    } catch (error) {
      console.error('Login error:', error);
      Alert.alert(
        'Error',
        error.response?.data?.error || 'Error al verificar patente',
      );
    } finally {
      setLoading(false);
    }
  };

  // Cerrar sesión
  const handleLogout = async () => {
    Alert.alert(
      'Cerrar Sesión',
      '¿Estás seguro que deseas cerrar sesión?',
      [
        {text: 'Cancelar', style: 'cancel'},
        {
          text: 'Cerrar Sesión',
          style: 'destructive',
          onPress: async () => {
            // Detener tracking si está activo
            if (isTracking) {
              await stopTracking();
            }
            
            // Limpiar datos guardados
            await AsyncStorage.clear();
            
            setIsAuthenticated(false);
            setDriverId(null);
            setDriverName('');
            setPatente('');
          },
        },
      ],
    );
  };

  // Enviar ubicación al servidor
  const sendLocationToServer = async (latitude, longitude, accuracy) => {
    try {
      const savedDriverId = await AsyncStorage.getItem('driverId');
      if (!savedDriverId) {
        console.log('No driver ID found');
        return;
      }

      await axios.post(
        `${API_BASE_URL}/api/drivers/${savedDriverId}/update-location/`,
        {
          lat: latitude,
          lng: longitude,
          accuracy: accuracy,
        },
      );
      
      console.log(`✅ Ubicación enviada: ${latitude}, ${longitude}`);
    } catch (error) {
      console.error('Error enviando ubicación:', error);
    }
  };

  // Tarea de background para GPS tracking
  const backgroundTask = async taskDataArguments => {
    const {delay} = taskDataArguments;
    
    await new Promise(async resolve => {
      // Bucle infinito para tracking continuo
      while (BackgroundService.isRunning()) {
        try {
          // Obtener ubicación actual
          Geolocation.getCurrentPosition(
            position => {
              const {latitude, longitude, accuracy} = position.coords;
              console.log('Nueva ubicación:', latitude, longitude);
              
              // Enviar al servidor
              sendLocationToServer(latitude, longitude, accuracy);
              
              // Actualizar última ubicación en estado (para mostrar en UI)
              setLastLocation({
                latitude,
                longitude,
                timestamp: new Date().toLocaleTimeString(),
              });
            },
            error => {
              console.error('Error obteniendo ubicación:', error);
            },
            {
              accuracy: {
                android: 'high',
                ios: 'best',
              },
              enableHighAccuracy: true,
              timeout: 15000,
              maximumAge: 10000,
              distanceFilter: 0,
              forceRequestLocation: true,
              forceLocationManager: false,
              showLocationDialog: true,
            },
          );
        } catch (error) {
          console.error('Error en background task:', error);
        }
        
        // Esperar antes de la siguiente actualización (30 segundos)
        await new Promise(r => setTimeout(r, delay));
      }
    });
  };

  // Iniciar tracking GPS en background
  const startTracking = async () => {
    // Solicitar permisos
    const hasPermission = await requestLocationPermission();
    if (!hasPermission) {
      Alert.alert(
        'Permiso Requerido',
        'Se necesita permiso de ubicación para el tracking GPS',
      );
      return;
    }

    try {
      // Opciones para el servicio de background
      const options = {
        taskName: 'SoptraLoc GPS Tracking',
        taskTitle: 'SoptraLoc - Tracking Activo',
        taskDesc: 'Rastreando ubicación del conductor',
        taskIcon: {
          name: 'ic_launcher',
          type: 'mipmap',
        },
        color: '#667eea',
        linkingURI: 'soptraloc://tracking',
        parameters: {
          delay: 30000, // 30 segundos entre actualizaciones
        },
      };

      // Iniciar servicio de background
      await BackgroundService.start(backgroundTask, options);
      setIsTracking(true);
      
      Alert.alert(
        'Tracking Iniciado',
        'El GPS está activo y funcionará incluso con la pantalla bloqueada',
      );
    } catch (error) {
      console.error('Error iniciando tracking:', error);
      Alert.alert('Error', 'No se pudo iniciar el tracking GPS');
    }
  };

  // Detener tracking GPS
  const stopTracking = async () => {
    try {
      await BackgroundService.stop();
      setIsTracking(false);
      setLastLocation(null);
      Alert.alert('Tracking Detenido', 'El GPS ha sido desactivado');
    } catch (error) {
      console.error('Error deteniendo tracking:', error);
    }
  };

  // Pantalla de login
  if (!isAuthenticated) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loginContainer}>
          <Text style={styles.title}>SoptraLoc Driver</Text>
          <Text style={styles.subtitle}>Ingresa la patente de tu vehículo</Text>
          
          <TextInput
            style={styles.input}
            placeholder="Ejemplo: ABCD12"
            value={patente}
            onChangeText={setPatente}
            autoCapitalize="characters"
            maxLength={10}
          />
          
          <TouchableOpacity
            style={[styles.button, loading && styles.buttonDisabled]}
            onPress={handleLogin}
            disabled={loading}>
            {loading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.buttonText}>Iniciar Sesión</Text>
            )}
          </TouchableOpacity>
          
          <View style={styles.infoBox}>
            <Text style={styles.infoTitle}>ℹ️ Información Importante</Text>
            <Text style={styles.infoText}>
              • Esta app requiere acceso a tu ubicación{'\n'}
              • El GPS funcionará incluso con la pantalla bloqueada{'\n'}
              • La patente debe coincidir con la asignada en el sistema
            </Text>
          </View>
        </View>
      </SafeAreaView>
    );
  }

  // Pantalla principal (dashboard)
  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.dashboardContainer}>
        <View style={styles.header}>
          <Text style={styles.welcomeText}>Bienvenido</Text>
          <Text style={styles.driverName}>{driverName}</Text>
          <Text style={styles.patenteText}>Patente: {patente}</Text>
        </View>

        <View style={styles.statusCard}>
          <Text style={styles.statusTitle}>Estado del GPS</Text>
          <View style={styles.statusIndicator}>
            <View
              style={[
                styles.statusDot,
                isTracking ? styles.statusActive : styles.statusInactive,
              ]}
            />
            <Text style={styles.statusText}>
              {isTracking ? 'Activo' : 'Inactivo'}
            </Text>
          </View>
          
          {lastLocation && (
            <View style={styles.locationInfo}>
              <Text style={styles.locationText}>
                📍 Última ubicación: {lastLocation.timestamp}
              </Text>
              <Text style={styles.locationCoords}>
                Lat: {lastLocation.latitude.toFixed(6)},{' '}
                Lng: {lastLocation.longitude.toFixed(6)}
              </Text>
            </View>
          )}
        </View>

        <TouchableOpacity
          style={[
            styles.button,
            styles.trackingButton,
            isTracking && styles.stopButton,
          ]}
          onPress={isTracking ? stopTracking : startTracking}>
          <Text style={styles.buttonText}>
            {isTracking ? '⏹️ Detener Tracking' : '▶️ Iniciar Tracking'}
          </Text>
        </TouchableOpacity>

        <View style={styles.infoBox}>
          <Text style={styles.infoTitle}>💡 Consejos</Text>
          <Text style={styles.infoText}>
            • Puedes bloquear la pantalla, el GPS seguirá activo{'\n'}
            • La app envía tu ubicación cada 30 segundos{'\n'}
            • Mantén el GPS del celular activado{'\n'}
            • Asegúrate de tener conexión a internet
          </Text>
        </View>

        <View style={styles.safetyBox}>
          <Text style={styles.safetyTitle}>🛡️ Seguridad Vial</Text>
          <Text style={styles.safetyText}>
            Recuerda: No uses el celular mientras conduces. Esta app funciona
            en segundo plano para tu seguridad.
          </Text>
        </View>

        <TouchableOpacity
          style={[styles.button, styles.logoutButton]}
          onPress={handleLogout}>
          <Text style={styles.buttonText}>Cerrar Sesión</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  loginContainer: {
    flex: 1,
    justifyContent: 'center',
    padding: 20,
  },
  dashboardContainer: {
    padding: 20,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#667eea',
    textAlign: 'center',
    marginBottom: 10,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 30,
  },
  input: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 15,
    fontSize: 18,
    borderWidth: 1,
    borderColor: '#ddd',
    marginBottom: 20,
  },
  button: {
    backgroundColor: '#667eea',
    borderRadius: 8,
    padding: 15,
    alignItems: 'center',
  },
  buttonDisabled: {
    backgroundColor: '#ccc',
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  header: {
    backgroundColor: '#667eea',
    borderRadius: 12,
    padding: 20,
    marginBottom: 20,
  },
  welcomeText: {
    color: '#fff',
    fontSize: 16,
    opacity: 0.9,
  },
  driverName: {
    color: '#fff',
    fontSize: 24,
    fontWeight: 'bold',
    marginVertical: 5,
  },
  patenteText: {
    color: '#fff',
    fontSize: 14,
    opacity: 0.8,
  },
  statusCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    marginBottom: 20,
    elevation: 2,
  },
  statusTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 10,
    color: '#333',
  },
  statusIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 8,
  },
  statusActive: {
    backgroundColor: '#4caf50',
  },
  statusInactive: {
    backgroundColor: '#f44336',
  },
  statusText: {
    fontSize: 16,
    color: '#666',
  },
  locationInfo: {
    marginTop: 15,
    padding: 10,
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
  },
  locationText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 5,
  },
  locationCoords: {
    fontSize: 12,
    color: '#999',
    fontFamily: 'monospace',
  },
  trackingButton: {
    marginBottom: 20,
  },
  stopButton: {
    backgroundColor: '#f44336',
  },
  infoBox: {
    backgroundColor: '#e3f2fd',
    borderRadius: 12,
    padding: 15,
    marginBottom: 15,
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1976d2',
    marginBottom: 8,
  },
  infoText: {
    fontSize: 14,
    color: '#555',
    lineHeight: 20,
  },
  safetyBox: {
    backgroundColor: '#fff3e0',
    borderRadius: 12,
    padding: 15,
    marginBottom: 15,
  },
  safetyTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#f57c00',
    marginBottom: 8,
  },
  safetyText: {
    fontSize: 14,
    color: '#555',
    lineHeight: 20,
  },
  logoutButton: {
    backgroundColor: '#757575',
  },
});

export default App;
