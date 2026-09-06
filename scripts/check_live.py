"""Read-only deployment smoke check. Does not create business records."""
import httpx

with httpx.Client(base_url='http://127.0.0.1:8080') as client:
    for path in ['/', '/login', '/register', '/static/styles.css', '/static/js/app.js', '/static/js/forms.js', '/static/js/views.js', '/static/js/api.js', '/static/js/ui.js', '/static/js/regions.js', '/api/health']:
        response = client.get(path)
        assert response.status_code == 200, (path, response.status_code)
    response = client.post('/api/auth/login', json={'username': 'admin', 'password': 'admin123'})
    assert response.status_code == 200
    client.headers['Authorization'] = 'Bearer ' + response.json()['access_token']
    for path in ['/api/auth/me', '/api/tasks', '/api/dashboard', '/api/personnel', '/api/users', '/api/meta/permissions', '/api/sampling']:
        response = client.get(path)
        assert response.status_code == 200, (path, response.status_code)
    assert '/api/auth/password' in client.get('/openapi.json').json()['paths']
    print('Live smoke check: 19 routes and login verified; no business data created.')
