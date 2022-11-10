a :- b. 
b :- a.
a :- not c.
b :- d.
b :- e. 
e :- b.
c :- not d.
d :- not c.
%c;d.
%%%
%a :- not not b. 
%b :- not not a.
%a :- not c.
%b :- not not d.
%c;d.
%b :- not not e. 
%e :- not not b.
