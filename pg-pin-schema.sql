--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET search_path = public, pg_catalog;

--
-- Name: english_ispell; Type: TEXT SEARCH DICTIONARY; Schema: public; Owner: postgres
--

CREATE TEXT SEARCH DICTIONARY english_ispell (
    TEMPLATE = pg_catalog.ispell,
    dictfile = 'english', afffile = 'english', stopwords = 'english' );


ALTER TEXT SEARCH DICTIONARY public.english_ispell OWNER TO postgres;

--
-- Name: simple_dict; Type: TEXT SEARCH DICTIONARY; Schema: public; Owner: postgres
--

CREATE TEXT SEARCH DICTIONARY simple_dict (
    TEMPLATE = pg_catalog.simple,
    stopwords = 'english' );


ALTER TEXT SEARCH DICTIONARY public.simple_dict OWNER TO postgres;

--
-- Name: my_config; Type: TEXT SEARCH CONFIGURATION; Schema: public; Owner: postgres
--

CREATE TEXT SEARCH CONFIGURATION my_config (
    PARSER = pg_catalog."default" );

ALTER TEXT SEARCH CONFIGURATION my_config
    ADD MAPPING FOR asciiword WITH english_ispell, english_stem;

ALTER TEXT SEARCH CONFIGURATION my_config
    ADD MAPPING FOR word WITH english_ispell, english_stem;

ALTER TEXT SEARCH CONFIGURATION my_config
    ADD MAPPING FOR numword WITH simple;

ALTER TEXT SEARCH CONFIGURATION my_config
    ADD MAPPING FOR email WITH simple;

ALTER TEXT SEARCH CONFIGURATION my_config
    ADD MAPPING FOR url WITH simple;

ALTER TEXT SEARCH CONFIGURATION my_config
    ADD MAPPING FOR host WITH simple;

ALTER TEXT SEARCH CONFIGURATION my_config
    ADD MAPPING FOR sfloat WITH simple;

ALTER TEXT SEARCH CONFIGURATION my_config
    ADD MAPPING FOR version WITH simple;

ALTER TEXT SEARCH CONFIGURATION my_config
    ADD MAPPING FOR hword_numpart WITH simple;

ALTER TEXT SEARCH CONFIGURATION my_config
    ADD MAPPING FOR hword_part WITH english_ispell, english_stem;

ALTER TEXT SEARCH CONFIGURATION my_config
    ADD MAPPING FOR hword_asciipart WITH english_ispell, english_stem;

ALTER TEXT SEARCH CONFIGURATION my_config
    ADD MAPPING FOR numhword WITH simple;

ALTER TEXT SEARCH CONFIGURATION my_config
    ADD MAPPING FOR asciihword WITH english_ispell, english_stem;

ALTER TEXT SEARCH CONFIGURATION my_config
    ADD MAPPING FOR hword WITH english_ispell, english_stem;

ALTER TEXT SEARCH CONFIGURATION my_config
    ADD MAPPING FOR url_path WITH simple;

ALTER TEXT SEARCH CONFIGURATION my_config
    ADD MAPPING FOR file WITH simple;

ALTER TEXT SEARCH CONFIGURATION my_config
    ADD MAPPING FOR "float" WITH simple;

ALTER TEXT SEARCH CONFIGURATION my_config
    ADD MAPPING FOR "int" WITH simple;

ALTER TEXT SEARCH CONFIGURATION my_config
    ADD MAPPING FOR uint WITH simple;


ALTER TEXT SEARCH CONFIGURATION public.my_config OWNER TO postgres;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: admin_roles; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE admin_roles (
    id integer NOT NULL,
    name character varying(30)
);


ALTER TABLE public.admin_roles OWNER TO postgres;

--
-- Name: admin_roles_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE admin_roles_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.admin_roles_id_seq OWNER TO postgres;

--
-- Name: admin_roles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE admin_roles_id_seq OWNED BY admin_roles.id;


--
-- Name: admin_users; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE admin_users (
    id integer NOT NULL,
    username text NOT NULL,
    pwsalt text NOT NULL,
    pwhash text NOT NULL,
    super boolean DEFAULT false,
    manager boolean DEFAULT false,
    site_user_id integer
);


ALTER TABLE public.admin_users OWNER TO postgres;

--
-- Name: admin_users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE admin_users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.admin_users_id_seq OWNER TO postgres;

--
-- Name: admin_users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE admin_users_id_seq OWNED BY admin_users.id;


--
-- Name: admin_users_roles; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE admin_users_roles (
    user_id integer NOT NULL,
    rol_id integer NOT NULL
);


ALTER TABLE public.admin_users_roles OWNER TO postgres;

--
-- Name: albums; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE albums (
    id integer NOT NULL,
    name text,
    user_id integer
);


ALTER TABLE public.albums OWNER TO postgres;

--
-- Name: albums_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE albums_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.albums_id_seq OWNER TO postgres;

--
-- Name: albums_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE albums_id_seq OWNED BY albums.id;


--
-- Name: boards; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE boards (
    id integer NOT NULL,
    name text,
    description text,
    user_id integer,
    public boolean DEFAULT true
);


ALTER TABLE public.boards OWNER TO postgres;

--
-- Name: boards_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE boards_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.boards_id_seq OWNER TO postgres;

--
-- Name: boards_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE boards_id_seq OWNED BY boards.id;


--
-- Name: categories; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE categories (
    id integer NOT NULL,
    name text
);


ALTER TABLE public.categories OWNER TO postgres;

--
-- Name: categories_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE categories_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.categories_id_seq OWNER TO postgres;

--
-- Name: categories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE categories_id_seq OWNED BY categories.id;


--
-- Name: category_register_thumbnails; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE category_register_thumbnails (
    id integer NOT NULL,
    category_id integer NOT NULL,
    image_name character varying(100) NOT NULL
);


ALTER TABLE public.category_register_thumbnails OWNER TO postgres;

--
-- Name: category_register_thumbnails_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE category_register_thumbnails_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.category_register_thumbnails_id_seq OWNER TO postgres;

--
-- Name: category_register_thumbnails_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE category_register_thumbnails_id_seq OWNED BY category_register_thumbnails.id;


--
-- Name: collected_data; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE collected_data (
    start integer NOT NULL,
    ellapsed_time integer NOT NULL
);


ALTER TABLE public.collected_data OWNER TO postgres;

--
-- Name: comments; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE comments (
    id integer NOT NULL,
    pin_id integer,
    user_id integer,
    comment text,
    "timestamp" integer DEFAULT date_part('epoch'::text, now())
);


ALTER TABLE public.comments OWNER TO postgres;

--
-- Name: comments_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE comments_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.comments_id_seq OWNER TO postgres;

--
-- Name: comments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE comments_id_seq OWNED BY comments.id;


--
-- Name: convos; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE convos (
    id integer NOT NULL,
    id1 integer,
    id2 integer
);


ALTER TABLE public.convos OWNER TO postgres;

--
-- Name: convos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE convos_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.convos_id_seq OWNER TO postgres;

--
-- Name: convos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE convos_id_seq OWNED BY convos.id;


--
-- Name: cool_pins; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE cool_pins (
    category_id integer NOT NULL,
    pin_id integer NOT NULL
);


ALTER TABLE public.cool_pins OWNER TO postgres;

--
-- Name: follows; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE follows (
    follower integer NOT NULL,
    follow integer NOT NULL
);


ALTER TABLE public.follows OWNER TO postgres;

--
-- Name: friends; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE friends (
    id1 integer NOT NULL,
    id2 integer NOT NULL,
    accepted integer DEFAULT 0
);


ALTER TABLE public.friends OWNER TO postgres;

--
-- Name: likes; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE likes (
    user_id integer NOT NULL,
    pin_id integer NOT NULL
);


ALTER TABLE public.likes OWNER TO postgres;

--
-- Name: media_servers; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE media_servers (
    id integer NOT NULL,
    active boolean DEFAULT true NOT NULL,
    url text NOT NULL,
    path text NOT NULL
);


ALTER TABLE public.media_servers OWNER TO postgres;

--
-- Name: media_servers_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE media_servers_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.media_servers_id_seq OWNER TO postgres;

--
-- Name: media_servers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE media_servers_id_seq OWNED BY media_servers.id;


--
-- Name: messages; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE messages (
    id integer NOT NULL,
    convo_id integer,
    sender integer,
    content text
);


ALTER TABLE public.messages OWNER TO postgres;

--
-- Name: messages_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE messages_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.messages_id_seq OWNER TO postgres;

--
-- Name: messages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE messages_id_seq OWNED BY messages.id;


--
-- Name: notifs; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE notifs (
    id integer NOT NULL,
    user_id integer,
    message text,
    link text,
    "timestamp" integer DEFAULT date_part('epoch'::text, now()),
    fr boolean DEFAULT false,
    fr_id integer
);


ALTER TABLE public.notifs OWNER TO postgres;

--
-- Name: notifs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE notifs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.notifs_id_seq OWNER TO postgres;

--
-- Name: notifs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE notifs_id_seq OWNED BY notifs.id;


--
-- Name: photos; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE photos (
    id integer NOT NULL,
    album_id integer,
    filename text DEFAULT ''::text NOT NULL,
    sizes text DEFAULT ''::text NOT NULL
);


ALTER TABLE public.photos OWNER TO postgres;

--
-- Name: photos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE photos_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.photos_id_seq OWNER TO postgres;

--
-- Name: photos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE photos_id_seq OWNED BY photos.id;


--
-- Name: pin_loader_log; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE pin_loader_log (
    pin_loader_id integer NOT NULL,
    pin_id integer NOT NULL,
    tstamp timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.pin_loader_log OWNER TO postgres;

--
-- Name: pins; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE pins (
    id integer NOT NULL,
    name text,
    description text,
    user_id integer,
    "timestamp" integer DEFAULT date_part('epoch'::text, now()),
    repin integer DEFAULT 0,
    link text DEFAULT ''::text,
    category integer DEFAULT 0,
    privacy smallint DEFAULT 0,
    views integer DEFAULT 0,
    tsv tsvector
);


ALTER TABLE public.pins OWNER TO postgres;

--
-- Name: pins_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE pins_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.pins_id_seq OWNER TO postgres;

--
-- Name: pins_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE pins_id_seq OWNED BY pins.id;


--
-- Name: pins_photos; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE pins_photos (
    pin_id integer,
    photo_id integer
);


ALTER TABLE public.pins_photos OWNER TO postgres;

--
-- Name: ratings; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE ratings (
    rating integer,
    user_id integer NOT NULL,
    pin_id integer NOT NULL
);


ALTER TABLE public.ratings OWNER TO postgres;

--
-- Name: tags; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE tags (
    pin_id integer NOT NULL,
    tags text
);


ALTER TABLE public.tags OWNER TO postgres;

--
-- Name: temp_pins; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE temp_pins (
    id integer NOT NULL,
    image text,
    link text,
    title text,
    category integer,
    description text,
    deleted boolean DEFAULT false
);


ALTER TABLE public.temp_pins OWNER TO postgres;

--
-- Name: temp_pins_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE temp_pins_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.temp_pins_id_seq OWNER TO postgres;

--
-- Name: temp_pins_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE temp_pins_id_seq OWNED BY temp_pins.id;


--
-- Name: user_prefered_categories; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE user_prefered_categories (
    user_id integer NOT NULL,
    category_id integer NOT NULL
);


ALTER TABLE public.user_prefered_categories OWNER TO postgres;

--
-- Name: user_prefered_pins; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE user_prefered_pins (
    user_id integer NOT NULL,
    pin_id integer NOT NULL
);


ALTER TABLE public.user_prefered_pins OWNER TO postgres;

--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE users (
    id integer NOT NULL,
    email text,
    name text,
    pw_hash text,
    pw_salt text,
    about text,
    "timestamp" integer DEFAULT date_part('epoch'::text, now()),
    views integer DEFAULT 0,
    show_views boolean DEFAULT true,
    username text,
    seriesid text DEFAULT ''::text,
    logintoken text DEFAULT ''::text,
    zip integer,
    country text DEFAULT ''::text,
    website text DEFAULT ''::text,
    facebook text DEFAULT ''::text,
    linkedin text DEFAULT ''::text,
    twitter text DEFAULT ''::text,
    gplus text DEFAULT ''::text,
    pic integer,
    hometown text,
    city text,
    private boolean DEFAULT false,
    bg boolean DEFAULT false,
    bgx integer DEFAULT 0,
    bgy integer DEFAULT 0,
    activation integer DEFAULT 0,
    tsv tsvector,
    login_source character(2) DEFAULT 'MP'::bpchar NOT NULL,
    birthday date,
    headerbgx integer DEFAULT 0 NOT NULL,
    headerbgy integer DEFAULT 0 NOT NULL,
    locale character(2) DEFAULT 'en'::bpchar NOT NULL
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE users_id_seq OWNED BY users.id;


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY admin_roles ALTER COLUMN id SET DEFAULT nextval('admin_roles_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY admin_users ALTER COLUMN id SET DEFAULT nextval('admin_users_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY albums ALTER COLUMN id SET DEFAULT nextval('albums_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY boards ALTER COLUMN id SET DEFAULT nextval('boards_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY categories ALTER COLUMN id SET DEFAULT nextval('categories_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY category_register_thumbnails ALTER COLUMN id SET DEFAULT nextval('category_register_thumbnails_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY comments ALTER COLUMN id SET DEFAULT nextval('comments_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY convos ALTER COLUMN id SET DEFAULT nextval('convos_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY media_servers ALTER COLUMN id SET DEFAULT nextval('media_servers_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY messages ALTER COLUMN id SET DEFAULT nextval('messages_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY notifs ALTER COLUMN id SET DEFAULT nextval('notifs_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY photos ALTER COLUMN id SET DEFAULT nextval('photos_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY pins ALTER COLUMN id SET DEFAULT nextval('pins_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY temp_pins ALTER COLUMN id SET DEFAULT nextval('temp_pins_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY users ALTER COLUMN id SET DEFAULT nextval('users_id_seq'::regclass);


--
-- Name: admin_roles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY admin_roles
    ADD CONSTRAINT admin_roles_pkey PRIMARY KEY (id);


--
-- Name: admin_users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY admin_users
    ADD CONSTRAINT admin_users_pkey PRIMARY KEY (id);


--
-- Name: admin_users_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY admin_users
    ADD CONSTRAINT admin_users_username_key UNIQUE (username);


--
-- Name: albums_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY albums
    ADD CONSTRAINT albums_pkey PRIMARY KEY (id);


--
-- Name: boards_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY boards
    ADD CONSTRAINT boards_pkey PRIMARY KEY (id);


--
-- Name: categories_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY categories
    ADD CONSTRAINT categories_pkey PRIMARY KEY (id);


--
-- Name: category_register_thumbnails_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY category_register_thumbnails
    ADD CONSTRAINT category_register_thumbnails_pkey PRIMARY KEY (id);


--
-- Name: comments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY comments
    ADD CONSTRAINT comments_pkey PRIMARY KEY (id);


--
-- Name: convos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY convos
    ADD CONSTRAINT convos_pkey PRIMARY KEY (id);


--
-- Name: follows_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY follows
    ADD CONSTRAINT follows_pkey PRIMARY KEY (follower, follow);


--
-- Name: friends_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY friends
    ADD CONSTRAINT friends_pkey PRIMARY KEY (id1, id2);


--
-- Name: likes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY likes
    ADD CONSTRAINT likes_pkey PRIMARY KEY (user_id, pin_id);


--
-- Name: media_servers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY media_servers
    ADD CONSTRAINT media_servers_pkey PRIMARY KEY (id);


--
-- Name: messages_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY messages
    ADD CONSTRAINT messages_pkey PRIMARY KEY (id);


--
-- Name: notifs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY notifs
    ADD CONSTRAINT notifs_pkey PRIMARY KEY (id);


--
-- Name: photos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY photos
    ADD CONSTRAINT photos_pkey PRIMARY KEY (id);


--
-- Name: pins_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY pins
    ADD CONSTRAINT pins_pkey PRIMARY KEY (id);


--
-- Name: ratings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY ratings
    ADD CONSTRAINT ratings_pkey PRIMARY KEY (user_id, pin_id);


--
-- Name: tags_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY tags
    ADD CONSTRAINT tags_pkey PRIMARY KEY (pin_id);


--
-- Name: temp_pins_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY temp_pins
    ADD CONSTRAINT temp_pins_pkey PRIMARY KEY (id);


--
-- Name: users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: id_cool_pins; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX id_cool_pins ON cool_pins USING btree (category_id);


--
-- Name: id_unique_cool_pins; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE UNIQUE INDEX id_unique_cool_pins ON cool_pins USING btree (category_id, pin_id);


--
-- Name: pk_admin_users_roles; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE UNIQUE INDEX pk_admin_users_roles ON admin_users_roles USING btree (user_id, rol_id);


--
-- Name: unique_user_prefered_categories; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE UNIQUE INDEX unique_user_prefered_categories ON user_prefered_categories USING btree (user_id, category_id);


--
-- Name: unique_user_prefered_pins; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE UNIQUE INDEX unique_user_prefered_pins ON user_prefered_pins USING btree (user_id, pin_id);


--
-- Name: users_username_idx; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX users_username_idx ON users USING btree (username);


--
-- Name: tsvectorupdate; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE ON pins FOR EACH ROW EXECUTE PROCEDURE tsvector_update_trigger('tsv', 'pg_catalog.english', 'description');


--
-- Name: tsvectorupdate_users; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER tsvectorupdate_users BEFORE INSERT OR UPDATE ON users FOR EACH ROW EXECUTE PROCEDURE tsvector_update_trigger('tsv', 'pg_catalog.english', 'name');


--
-- Name: admin_users_roles_rol_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY admin_users_roles
    ADD CONSTRAINT admin_users_roles_rol_id_fkey FOREIGN KEY (rol_id) REFERENCES admin_roles(id);


--
-- Name: admin_users_roles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY admin_users_roles
    ADD CONSTRAINT admin_users_roles_user_id_fkey FOREIGN KEY (user_id) REFERENCES admin_users(id);


--
-- Name: admin_users_site_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY admin_users
    ADD CONSTRAINT admin_users_site_user_id_fkey FOREIGN KEY (site_user_id) REFERENCES users(id);


--
-- Name: category_register_thumbnails_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY category_register_thumbnails
    ADD CONSTRAINT category_register_thumbnails_category_id_fkey FOREIGN KEY (category_id) REFERENCES categories(id);


--
-- Name: cool_pins_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY cool_pins
    ADD CONSTRAINT cool_pins_category_id_fkey FOREIGN KEY (category_id) REFERENCES categories(id);


--
-- Name: cool_pins_pin_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY cool_pins
    ADD CONSTRAINT cool_pins_pin_id_fkey FOREIGN KEY (pin_id) REFERENCES pins(id);


--
-- Name: pin_loader_log_pin_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY pin_loader_log
    ADD CONSTRAINT pin_loader_log_pin_id_fkey FOREIGN KEY (pin_id) REFERENCES pins(id);


--
-- Name: pin_loader_log_pin_loader_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY pin_loader_log
    ADD CONSTRAINT pin_loader_log_pin_loader_id_fkey FOREIGN KEY (pin_loader_id) REFERENCES admin_users(id);


--
-- Name: pins_photos_photo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY pins_photos
    ADD CONSTRAINT pins_photos_photo_id_fkey FOREIGN KEY (photo_id) REFERENCES photos(id);


--
-- Name: pins_photos_pin_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY pins_photos
    ADD CONSTRAINT pins_photos_pin_id_fkey FOREIGN KEY (pin_id) REFERENCES pins(id);


--
-- Name: user_prefered_categories_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY user_prefered_categories
    ADD CONSTRAINT user_prefered_categories_category_id_fkey FOREIGN KEY (category_id) REFERENCES categories(id);


--
-- Name: user_prefered_categories_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY user_prefered_categories
    ADD CONSTRAINT user_prefered_categories_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);


--
-- Name: user_prefered_pins_pin_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY user_prefered_pins
    ADD CONSTRAINT user_prefered_pins_pin_id_fkey FOREIGN KEY (pin_id) REFERENCES pins(id);


--
-- Name: user_prefered_pins_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY user_prefered_pins
    ADD CONSTRAINT user_prefered_pins_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--



alter table users add is_pin_loader boolean not null default FALSE;


create table password_change_tokens (
	id serial primary key,
	user_id integer not null,
	token char(20) not null,
	created_on timestamp not null default now(),
	valid_hours int not null default 48,
	used boolean not null default(FALSE),
	used_on timestamp null
);
