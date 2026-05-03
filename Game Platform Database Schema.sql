-- Game Platform Database Schema

drop database if exists game_platform;
create database game_platform;
use game_platform;

-----------------------
-- Table DDL (7 Tables)
-----------------------

-- 1. Users
create table Users (
	user_id		int primary key auto_increment,
    username	varchar(50)		not null unique,
    email		varchar(100)	not null unique,
    join_date	date			not null default (current_date)
);

-- 2. Games
create table Games (
	game_id		int primary key	auto_increment,
    title		varchar(100)	not null,
    genre		varchar(50),
    price		decimal(6, 2)	not null default 0.00,
    release_date	date
);

-- 3. Purchases
create table Purchases (
	purchase_id	int primary key auto_increment,
    user_id		int				not null,
    game_id		int				not null,
    purchased_at datetime		not null default current_timestamp,
    amount_paid	decimal(6, 2)	not null,
    foreign key (user_id) references Users(user_id) on delete cascade,
    foreign key (game_id) references Games(game_id) on delete cascade,
    unique (user_id, game_id)  -- a user can only buy a game once
);

-- 4. GameSessions
create table GameSessions (
	session_id	int primary key	auto_increment,
    user_id		int				not null,
    game_id		int				not null,
    start_time	datetime		not null default current_timestamp,
    end_time	datetime,
    score		int				not null default 0,
    foreign key (user_id) references Users(user_id) on delete cascade,
    foreign key(game_id) references Games(game_id) on delete cascade
);

-- 5. Achievements
create table Achievements (
	achievement_id	int primary key auto_increment,
    game_id			int				not null,
    name			varchar(100)	not null,
    description		varchar(255),
    points			int				not null default 10,
    score_required	int				not null default 0,
    foreign key(game_id) references Games(game_id) on delete cascade
);

-- 6. UserAchievements	(junction table)
create table UserAchievements (
	user_id			int			not null,
    achievement_id	int			not null,
    earned_at		datetime	not null default current_timestamp,
    primary key (user_id, achievement_id),
    foreign key (user_id)			references Users(user_id)				on delete cascade,
    foreign key (achievement_id)	references Achievements(achievement_id)	on delete cascade
);

-- 7. Friends	(self-referencing junction)
create table Friends (
	user_id		int		not null,
    friend_id	int		not null,
    since_date	date	not null default (current_date),
    primary key (user_id, friend_id),
    foreign key (user_id)	references Users(user_id) on delete cascade,
    foreign key (friend_id)	references Users(user_id) on delete cascade,
    check (user_id <> friend_id)
);

-----------
-- View DDL
-----------

-- View 1: Leaderboard - top scores per game with player info
create or replace view vw_Leaderboard as
select
	g.title as game_title,
    u.username,
    max(gs.score) as best_score,
    count(gs.session_id) as total_sessions,
    round(sum(timestampdiff(minute, gs.start_time, gs.end_time)) / 60.0, 2) as total_hours,
    rank() over (
		partition by g.game_id
        order by max(gs.score) desc) as game_rank
from GameSessions gs
join Users u on gs.user_id = u.user_id
join Games g on gs.game_id = g.game_id
where gs.end_time is not null
group by g.game_id, g.title, u.user_id, u.username;

-- View 2: User summary - playtime, spending, and achievement points
create or replace view vw_UserSummary as
select
	u.user_id,
    u.username,
    u.email,
    u.join_date,
    count(distinct p.game_id)	as games_owned,
    coalesce(sum(p.amount_paid), 0)	as total_spent,
    count(distinct gs.session_id)	as total_sessions,
    round(coalesce(sum(timestampdiff(minute, gs.start_time, gs.end_time)), 0) / 60.0, 2) as total_hours,
    coalesce(sum(a.points), 0)		as achievement_points
from Users u
left join Purchases p on u.user_id = p.user_id
left join GameSessions gs on u.user_id = gs.user_id and gs.end_time is not null
left join UserAchievements ua on u.user_id = ua.user_id
left join Achievements a on ua.achievement_id = a.achievement_id
group by u.user_id, u.username, u.email, u.join_date;

---------------
-- Function DDL
---------------

delimiter $$

-- Function: return total playtime (in hours) for a given user
create function GetTotalPlaytime(p_user_id int)
returns decimal (8, 2)
reads sql data
deterministic
begin
	declare total_hours decimal(8, 2);
    
    select round(coalesce(sum(timestampdiff(minute, start_time, end_time)), 0) / 60.0, 2)
    into total_hours
    from GameSessions
    where user_id = p_user_id
    and end_time is not null;
    
    return total_hours;
end$$

delimiter ;

----------------
-- Procedure DDL
----------------

delimiter $$

-- Procedure 1: Add a mutual friendship (both directions at once)
create procedure AddFriend(
	in p_user_id	int,
    in p_friend_id	int
)
begin
	-- Guard: don't insert if already freinds
    if not exists (
		select 1 from Friends
        where user_id = p_user_id and friend_id = p_friend_id
	) then
		insert into Friends (user_id, friend_id) values (p_user_id, p_friend_id);
        insert into Friends (user_id, friend_id) values (p_friend_id, p_user_id);
	end if;
end$$

-- Procedure 2: Remove a mutual friendship (both directions)
create procedure RemoveFriend(
	in p_user_id	int,
    in p_friend_id	int
)
begin
	delete from Friends
    where (user_id = p_user_id	and friend_id = p_friend_id)
	or (user_id = p_friend_id	and friend_id = p_user_id);
end$$

delimiter ;


--------------
-- Trigger DDL
--------------

delimiter $$

-- Trigger: after a session ends, auto-award achievements whose
-- score_required threshold the player just met for the first time
create trigger trg_AutoAwardAchievement
after insert on GameSessions
for each row
begin
	-- insert any ahcievement for this game whose threshold the score meets,
    -- but only if the user hasn't already earned them
    insert ignore into UserAchievements (user_id, achievement_id, earned_at)
    select new.user_id, a.achievement_id, now()
    from Achievements a
    where a.game_id = new.game_id
    and a.score_required <= new.score;
end$$

delimiter ;


-- ------------
-- Sample Data
-- ------------

insert into Users (username, email, join_date) values
	('alice',	'alice@email.com',	'2024-01-10'),
    ('bob',		'bob@email.com',	'2024-02-14'),
    ('carol',	'carol@email.com',	'2024-03-05'),
    ('dave',	'dave@email.com',	'2025-04-20'),
    ('eve',		'eve@email.com',	'2025-05-01');

insert into Games (title, genre, price, release_date) values
	('Shadow Quest',	'RPG',	19.99,	'2023-06-15'),
    ('Turbo Racers',	'Racing',	14.99,	'2023-08-11'),
    ('Dungeon',			'Rouguelike',	9.99,	'2022-09-12'),
    ('Star Command',	'Strategy',	24.99,		'2025-01-30');

insert into Purchases (user_id, game_id, amount_paid) values
	(1, 1, 19.99),	(1, 2, 14.99),	(1, 3, 9.99),
    (2, 1, 19.99),	(2, 4, 24.99),
    (3, 2, 14.99),	(3, 3, 9.99),
    (4, 1, 19.99),	(4, 3, 9.99),
    (5, 4, 24.99);

insert into Achievements (game_id, name, description, points, score_required) values
	(1,	'First Blood',	'Score 100 points',		10,	100),
    (1,	'Shadow Master',	'Score 1000 points',	50,	1000),
    (2,	'Pole Position',	'Score 500 points',		20,	500),
    (3,	'Dungeon Crawler',	'Score 300 points',		15,	300),
    (3,	'Dungeon Lord',		'Score 1500 points',	75,	1500),
    (4,	'First Contact',	'Score 200 points',		10,	200);

insert into GameSessions (user_id, game_id, start_time, end_time, score) values
	(1,	1,	'2024-06-01 10:00:00',	'2024-06-01 11:30:00',	850),
    (1, 2, '2024-06-02 14:00:00',	'2024-06-02 15:00:00',	620),
    (2,	1,	'2024-06-03 09:00:00',	'2024-06-03 11:00:00',	1200),
    (3,	2,	'2024-06-04 16:00:00',	'2024-06-04 17:30:00',	480),
    (4,	3,	'2024-06-05 18:00:00',	'2024-06-05 19:45:00',	1600),
    (5,	4,	'2024-06-06 20:00:00',	'2024-06-06 21:00:00',	300),
    (1,	3,	'2024-06-07 12:00:00',	'2024-06-07 13:00:00',	310),
    (2,	4,	'2024-06-08 10:00:00',	'2024-06-08 11:30:00',	250);

call AddFriend(1, 2);
call AddFriend(1, 3);
call AddFriend(2, 4);


--------------------------------
-- Reports (Aggregation Queries)
--------------------------------

-- Report 1: Revenue by genre
select g.genre,
		count(distinct p.purchase_id) as total_purchases,
        sum(p.amount_paid) as total_revenue,
        round(avg(p.amount_paid), 2) as avg_sale_price
from Purchases p
join Games g on p.game_id = g.game_id
group by g.genre
order by total_revenue desc;

-- Report 2: Top users by achievement points
select u.username,
		count(ua.achievement_id) as achievements_earned,
        sum(a.points) as total_points,
        GetTotalPlaytime(u.user_id) as hours_played
from Users u
join UserAchievements ua on u.user_id = ua.user_id
join Achievements a on ua.achievement_id = a.achievement_id
group by u.user_id, u.username
order by total_points desc;

-- Report 3; Average score and session count per game
select g.title,
		count(gs.session_id) as total_sessions,
        round(avg(gs.score), 0) as avg_score,
        max(gs.score) as top_score,
        round(avg(timestampdiff(minute, gs.start_time, gs.end_time)), 0) as avg_session_min
from Games g
left join GameSessions gs on g.game_id = gs.game_id and gs.end_time is not null
group by g.game_id, g.title
order by avg_score desc;