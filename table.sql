create table lag_log (
    name text not null,
    moment timestamp with time zone not null,
    lag integer not null,
    master text null
);
