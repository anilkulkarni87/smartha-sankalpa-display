"""Offline city catalogue: approximate city-centre coordinates and IANA zones."""
LOCATIONS = [
    ('bellevue', 'Bellevue, WA', 'United States', 47.6101, -122.2015, 'America/Los_Angeles'),
    ('seattle', 'Seattle, WA', 'United States', 47.6062, -122.3321, 'America/Los_Angeles'),
    ('san-francisco', 'San Francisco, CA', 'United States', 37.7749, -122.4194, 'America/Los_Angeles'),
    ('los-angeles', 'Los Angeles, CA', 'United States', 34.0522, -118.2437, 'America/Los_Angeles'),
    ('new-york', 'New York, NY', 'United States', 40.7128, -74.0060, 'America/New_York'),
    ('chicago', 'Chicago, IL', 'United States', 41.8781, -87.6298, 'America/Chicago'),
    ('dallas', 'Dallas, TX', 'United States', 32.7767, -96.7970, 'America/Chicago'),
    ('toronto', 'Toronto', 'Canada', 43.6532, -79.3832, 'America/Toronto'),
    ('vancouver', 'Vancouver', 'Canada', 49.2827, -123.1207, 'America/Vancouver'),
    ('bengaluru', 'Bengaluru', 'India', 12.9716, 77.5946, 'Asia/Kolkata'),
    ('mysuru', 'Mysuru', 'India', 12.2958, 76.6394, 'Asia/Kolkata'),
    ('chennai', 'Chennai', 'India', 13.0827, 80.2707, 'Asia/Kolkata'),
    ('hyderabad', 'Hyderabad', 'India', 17.3850, 78.4867, 'Asia/Kolkata'),
    ('mumbai', 'Mumbai', 'India', 19.0760, 72.8777, 'Asia/Kolkata'),
    ('new-delhi', 'New Delhi', 'India', 28.6139, 77.2090, 'Asia/Kolkata'),
    ('london', 'London', 'United Kingdom', 51.5074, -0.1278, 'Europe/London'),
    ('sydney', 'Sydney', 'Australia', -33.8688, 151.2093, 'Australia/Sydney'),
    ('melbourne', 'Melbourne', 'Australia', -37.8136, 144.9631, 'Australia/Melbourne'),
    ('singapore', 'Singapore', 'Singapore', 1.3521, 103.8198, 'Asia/Singapore'),
    ('dubai', 'Dubai', 'United Arab Emirates', 25.2048, 55.2708, 'Asia/Dubai'),
]
CITIES = {
    key: dict(id=key, city=city, country=country, latitude=lat, longitude=lon, timezone=tz)
    for key, city, country, lat, lon, tz in LOCATIONS
}
