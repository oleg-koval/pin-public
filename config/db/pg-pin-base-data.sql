---
--- This file contains the base data required for mypinnings.com to function
---

--- Camilo's changes to have a scalable image upload/serving strategy
delete from media_servers;
insert into media_servers(url, path) values
('http://32.media.mypinnings.com', '32.media.mypinnings.com');

