---
--- This file contains the base data required for mypinnings.com to function
---

--- Camilo's changes to have a scalable image upload/serving strategy
insert into media_servers(url, path) values
('http://mypinnings.com/static/media/{path}/{media}', 'static/media/');

