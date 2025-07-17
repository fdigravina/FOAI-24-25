% Predicato per trovare i k nodi più vicini
k_nearest_neighbors(Node, K, NeighborsNodes) :-
    findall(OtherNode-Cost, (arco(Node, OtherNode, Cost), situazione(OtherNode, _), OtherNode \= Node), NeighborsWithCost),
    sort(2, @=<, NeighborsWithCost, SortedNeighbors), % Ordina in base al costo
    take(K, SortedNeighbors, Neighbors),
    extract_nodes(Neighbors, NeighborsNodes),
    write('Per il nodo '), write(Node), write(' i vicini sono: '), write(NeighborsNodes), nl.

% Predicato per prendere i primi K elementi di una lista
take(0, _, []) :- !.
take(_, [], []) :- !.
take(K, [H|T], [H|Rest]) :-
    K1 is K - 1,
    take(K1, T, Rest).

% Predicato per estrarre solo i nodi da una lista di coppie nodo-peso
extract_nodes([], []).
extract_nodes([Node-_ | Rest], [Node | Nodes]) :-
    extract_nodes(Rest, Nodes).

% Predicato per ottenere il secondo elemento della coppia nella prima posizione
secondo_elemento([(_, Secondo) | _], Secondo).

% Predicato per predire la situazione meteorologica di un nodo basata sui suoi k vicini
predict_weather(Node, K, Weather) :-
    k_nearest_neighbors(Node, K, Neighbors),
    find_most_common_weather(Neighbors, MostCommonWeather),
    secondo_elemento(MostCommonWeather, Weather).
    %write(MostCommonWeather), nl, write(Weather), nl.

% Predicato per determinare la situazione meteorologica più comune tra i vicini
find_most_common_weather(Neighbors, MostCommonWeather) :-
    conteggio_meteo(Neighbors, ListaConteggiMeteo),
    sort(ListaConteggiMeteo, SortedCounts),
    reverse(SortedCounts, DescendingCounts),
    write('Meteo dei vicini e conteggio: '), write(DescendingCounts), nl,
    prioritize_weather(DescendingCounts, MostCommonWeather).

% Predicato per contare il numero di occorrenze di ciascun tipo di meteo
conteggio_meteo([], []).
conteggio_meteo([Nodo|Resto], ListaConteggio) :-
    conteggio_meteo(Resto, ListaConteggioResto),
    (situazione(Nodo, Meteo) ->
        (aggiorna_conteggio(Meteo, ListaConteggioResto, ListaConteggioAggiornata),
        ListaConteggio = ListaConteggioAggiornata);
        ListaConteggio = ListaConteggioResto).

% Predicato ausiliario per aggiornare il conteggio
aggiorna_conteggio(Meteo, [], [(1, Meteo)]).
aggiorna_conteggio(Meteo, [(Conteggio, Meteo)|Resto], [(NuovoConteggio, Meteo)|Resto]) :-
    NuovoConteggio is Conteggio + 1.
aggiorna_conteggio(Meteo, [(Conteggio, AltroMeteo)|Resto], [(Conteggio, AltroMeteo)|RestoAggiornato]) :-
    Meteo \= AltroMeteo,
    aggiorna_conteggio(Meteo, Resto, RestoAggiornato).

% Predicato per trovare il massimo conteggio nella lista di tuple (conteggio, situazione)
max_count([], 0).
max_count([(Count, _)|T], MaxCount) :-
    max_count(T, MaxCountT),
    MaxCount is max(Count, MaxCountT).

% Predicato per filtrare la lista mantenendo solo gli elementi con il massimo conteggio
filter_max([], _, []).
filter_max([(Count, Situation)|T], MaxCount, [(Count, Situation)|Filtered]) :-
    Count =:= MaxCount,
    filter_max(T, MaxCount, Filtered).
filter_max([(Count, _)|T], MaxCount, Filtered) :-
    Count \= MaxCount,
    filter_max(T, MaxCount, Filtered).

% Definizione delle priorità delle situazioni
priority(pioggia_forte, 4).
priority(pioggia_media, 3).
priority(pioggia_lieve, 2).
priority(sole, 1).

% Predicato per confrontare le priorità degli elementi
compare_priority(Risultato, (_, Situazione1), (_, Situazione2)) :-
    priority(Situazione1, Priorita1),
    priority(Situazione2, Priorita2),
    %write(Situazione1), nl, write(Situazione2), nl,
    %write(Priorita1), nl, write(Priorita2), nl,
    (   Priorita1 > Priorita2 ->
        Risultato = '<'
    ;   Priorita1 < Priorita2 ->
        Risultato = '>'
    ).

% Predicato per ordinare la lista in base alla priorità della situazione
prioritize_weather(Counts, Prioritized) :-
    max_count(Counts, MaxCount),
    filter_max(Counts, MaxCount, Filtered),
    %write(Filtered), nl,
    predsort(compare_priority, Filtered, Prioritized),
    write('Priorita ordinata e filtrata: '), write(Prioritized), nl.

process_nodes([], _). % Base case: la lista dei nodi è vuota, non c'è nulla da scrivere sul file
process_nodes([Node|Rest], Stream) :-
    predict_weather(Node, 5, Weather),
    format('Meteo per il nodo ~w: ~w~n', [Node, Weather]),
    format(Stream, 'Meteo per il nodo ~w: ~w~n', [Node, Weather]), % Scrive sul file
    process_nodes(Rest, Stream).

main :-
    consult('code/predici.pl'),
    open('data/predizione.txt', write, Stream), % Apre il file in modalità di scrittura
    findall(Node, (arco(Node, _, _), \+ situazione(Node, _)), Nodes), % Trova tutti i nodi senza situazione
    list_to_set(Nodes, UniqueNodes), % Rimuove i duplicati
    process_nodes(UniqueNodes, Stream), % Passa lo stream del file come argomento
    close(Stream). % Chiude il file dopo aver scritto tutti i risultati