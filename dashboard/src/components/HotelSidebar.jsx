export default function HotelSidebar({ hotels, selectedHotel, onSelect, open, onClose }) {
  return (
    <>
      <div className={`sidebar ${open ? 'open' : ''}`}>
        <h3>Hotels</h3>
        <ul>
          {hotels.map((hotel) => (
            <li
              key={hotel.hotel_name}
              className={hotel.hotel_name === selectedHotel ? 'active' : ''}
              onClick={() => onSelect(hotel.hotel_name)}
            >
              <span className="hotel-name">{hotel.hotel_name}</span>
              <span className="hotel-count">{hotel.review_count}</span>
            </li>
          ))}
        </ul>
      </div>
      {open && <div className="sidebar-overlay" onClick={onClose} />}
    </>
  );
}