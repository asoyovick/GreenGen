import { useEffect, useMemo, useRef, useState } from "react";
import { api } from "../api.js";
import { PLACES, searchPlaces } from "../data/places.js";
import { coordLabel, parseCoordinateInput } from "../lib/coords.js";

export default function SearchControl({ onSelect, placesAvailable = false, selectLevel = "region" }) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [message, setMessage] = useState("");
  const [remotePlaces, setRemotePlaces] = useState([]);
  const [loading, setLoading] = useState(false);
  const timer = useRef(null);

  const coordinates = useMemo(() => parseCoordinateInput(query), [query]);
  const localPlaces = useMemo(
    () => (!placesAvailable && query.trim().length > 1 ? searchPlaces(query, 6) : []),
    [query, placesAvailable],
  );

  useEffect(() => {
    if (!placesAvailable) {
      setRemotePlaces([]);
      return undefined;
    }
    const q = query.trim();
    if (q.length < 2 || coordinates) {
      setRemotePlaces([]);
      return undefined;
    }
    clearTimeout(timer.current);
    timer.current = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await api.placesSearch(q, selectLevel, 8);
        setRemotePlaces(res.results || []);
      } catch {
        setRemotePlaces([]);
      } finally {
        setLoading(false);
      }
    }, 180);
    return () => clearTimeout(timer.current);
  }, [query, placesAvailable, selectLevel, coordinates]);

  const options = useMemo(() => {
    const items = [];
    if (coordinates) {
      items.push({
        type: "coordinate",
        id: "coordinate-option",
        label: coordLabel(coordinates.lat, coordinates.lon),
        detail: "Resolve typed coordinates to a place",
        lat: coordinates.lat,
        lon: coordinates.lon,
      });
    }
    if (placesAvailable) {
      for (const place of remotePlaces) {
        items.push({
          type: "place",
          id: `place-${place.id}`,
          placeId: place.id,
          place,
          label: place.name,
          detail: place.hierarchy || place.level,
          lat: place.centroid?.[1],
          lon: place.centroid?.[0],
        });
      }
    } else {
      for (const place of localPlaces) {
        items.push({
          type: "local",
          id: `local-${place.name}-${place.country}`,
          label: place.name,
          detail: place.country,
          lat: place.lat,
          lon: place.lon,
          name: place.name,
        });
      }
    }
    return items.filter((o) => Number.isFinite(o.lat) && Number.isFinite(o.lon));
  }, [coordinates, remotePlaces, localPlaces, placesAvailable]);

  function choose(option) {
    if (!option) return;
    onSelect(option, { fly: true, zoom: option.type === "coordinate" ? 3.2 : 4.0 });
    setMessage(`Selected ${option.label}${option.detail ? ` — ${option.detail}` : ""}.`);
    setQuery("");
    setOpen(false);
    setActiveIndex(-1);
  }

  function submit(event) {
    event.preventDefault();
    if (activeIndex >= 0 && options[activeIndex]) return choose(options[activeIndex]);
    if (options[0]) return choose(options[0]);
    if (!query.trim()) return;
    setMessage(`No place or coordinate match for “${query.trim()}”.`);
  }

  function onKeyDown(event) {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setOpen(true);
      setActiveIndex((index) => Math.min(index + 1, options.length - 1));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex((index) => Math.max(index - 1, 0));
    } else if (event.key === "Escape") {
      setOpen(false);
      setActiveIndex(-1);
    }
  }

  const showResults = open && query.trim().length > 0;

  return (
    <div
      className="search-panel"
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false);
      }}
    >
      <form className="search-panel__row" onSubmit={submit} role="search">
        <label className="sr-only" htmlFor="place-search">Search for a place or type coordinates</label>
        <input
          id="place-search"
          type="text"
          value={query}
          placeholder={placesAvailable ? `Search ${selectLevel}s or type 55.5, 70.2` : "Search a place or type 55.5, 70.2"}
          autoComplete="off"
          role="combobox"
          aria-expanded={showResults}
          aria-controls="place-search-results"
          aria-autocomplete="list"
          aria-activedescendant={showResults && activeIndex >= 0 ? options[activeIndex]?.id : undefined}
          aria-describedby="place-search-hint"
          onChange={(event) => {
            setQuery(event.target.value);
            setOpen(true);
            setActiveIndex(-1);
            setMessage("");
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={onKeyDown}
        />
        <button type="submit" className="button button--primary">Go</button>
      </form>
      <p id="place-search-hint" className="field-help">
        {placesAvailable ? "Search named places (offline gazetteer) or enter coordinates to resolve to a place." : "Offline gazetteer and coordinate entry."}
        {loading ? " Searching…" : ""}
      </p>
      {showResults && (
        <ul id="place-search-results" className="search-results" role="listbox">
          {options.length === 0 ? (
            <li className="search-results__empty" role="option" aria-disabled="true">No matches yet.</li>
          ) : (
            options.map((option, index) => (
              <li key={option.id} role="option" aria-selected={index === activeIndex} id={option.id}>
                <button
                  type="button"
                  className={`search-result ${index === activeIndex ? "search-result--active" : ""}`}
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => choose(option)}
                >
                  <span className="search-result__label">{option.label}</span>
                  <span className="search-result__detail">{option.detail}</span>
                </button>
              </li>
            ))
          )}
        </ul>
      )}
      {message && <p className="field-help" aria-live="polite">{message}</p>}
    </div>
  );
}
