import { useMemo, useRef, useState } from "react";
import { PLACES, searchPlaces } from "../data/places.js";
import { coordLabel, parseCoordinateInput } from "../lib/coords.js";

export default function SearchControl({ onSelect }) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [message, setMessage] = useState("");
  const inputRef = useRef(null);

  const coordinates = useMemo(() => parseCoordinateInput(query), [query]);
  const places = useMemo(
    () => (query.trim().length > 1 ? searchPlaces(query, 6) : []),
    [query],
  );

  const options = useMemo(() => {
    const items = [];
    if (coordinates) {
      items.push({
        type: "coordinate",
        id: "coordinate-option",
        label: coordLabel(coordinates.lat, coordinates.lon),
        detail: "Go to typed coordinates",
        lat: coordinates.lat,
        lon: coordinates.lon,
      });
    }
    for (const place of places) {
      items.push({
        type: "place",
        id: `place-${place.name}-${place.country}`,
        label: place.name,
        detail: place.country,
        lat: place.lat,
        lon: place.lon,
        name: place.name,
      });
    }
    return items;
  }, [coordinates, places]);

  function choose(option) {
    if (!option) return;
    onSelect(
      {
        lat: option.lat,
        lon: option.lon,
        label: option.type === "place" ? `${option.name}, ${option.detail}` : null,
      },
      { fly: true, zoom: option.type === "coordinate" ? 3.2 : 3.6 },
    );
    setMessage(`Moved to ${option.label}${option.type === "place" ? `, ${option.detail}` : ""}.`);
    setQuery("");
    setOpen(false);
    setActiveIndex(-1);
  }

  function submit(event) {
    event.preventDefault();
    if (activeIndex >= 0 && options[activeIndex]) {
      choose(options[activeIndex]);
      return;
    }
    if (options[0]) {
      choose(options[0]);
      return;
    }
    if (!query.trim()) return;
    setMessage(
      `No place or coordinate match for “${query.trim()}”. Try a city name, or coordinates such as 55.5, 70.2 or 55.5N 70.2E.`,
    );
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
        <label className="sr-only" htmlFor="place-search">
          Search for a place or type coordinates
        </label>
        <input
          ref={inputRef}
          id="place-search"
          type="text"
          value={query}
          placeholder="Search a place or type 55.5, 70.2"
          autoComplete="off"
          role="combobox"
          aria-expanded={showResults}
          aria-controls="place-search-results"
          aria-autocomplete="list"
          aria-activedescendant={
            showResults && activeIndex >= 0
              ? options[activeIndex]?.id
              : undefined
          }
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
        <button type="submit" className="button button--primary" aria-label="Go">
          Go
        </button>
      </form>

      {showResults && (
        <ul className="search-results" id="place-search-results" role="listbox">
          {options.map((option, index) => (
            <li key={option.id} role="presentation">
              <button
                id={option.id}
                type="button"
                role="option"
                aria-selected={index === activeIndex}
                tabIndex={-1}
                className={index === activeIndex ? "is-active" : ""}
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => choose(option)}
                onMouseEnter={() => setActiveIndex(index)}
              >
                <strong>{option.label}</strong>
                <span>{option.detail}</span>
              </button>
            </li>
          ))}
        </ul>
      )}

      {showResults && options.length === 0 && (
        <p className="search-empty">
          No offline gazetteer match. Coordinates such as 55.5, 70.2 or 55.5N
          70.2E work anywhere on Earth.
        </p>
      )}

      <p className="search-hint" id="place-search-hint">
        Offline gazetteer ({PLACES.length} places) plus coordinate entry. No
        external geocoder is called.
      </p>
      {message && (
        <p className="search-message" role="status" aria-live="polite">
          {message}
        </p>
      )}
    </div>
  );
}
