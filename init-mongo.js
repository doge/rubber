db.createUser({
  user: 'root',
  pwd: 'toor',
  roles: [
    {
      role: 'readWrite',
      db: 'image-host',
    },
  ],
});

db.createCollection('users', { capped: false });

db.users.insert([
  { 
	'username': 'admin',
	'email': 'admin@example.com',
	'role': 'admin',
	// 'admin'
	'password': '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918',
	'banned': false,
	'token': 'regenerate-me'
  }
]);