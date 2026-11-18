// GPS works without mobile data; these helpers format and compare positions.
export function getPosition(timeout = 20000) {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) return reject(new Error("위치 기능이 없어요"));
    navigator.geolocation.getCurrentPosition(resolve, reject, { enableHighAccuracy: true, timeout, maximumAge: 15000 });
  });
}

export function watchPosition(onPos, onErr) {
  if (!navigator.geolocation) {
    onErr && onErr(new Error("위치 기능이 없어요"));
    return () => {};
  }
  const id = navigator.geolocation.watchPosition(onPos, (e) => onErr && onErr(e), {
    enableHighAccuracy: true, maximumAge: 5000, timeout: 60000,
  });
  return () => navigator.geolocation.clearWatch(id);
}

export function posErrorText(e) {
  if (!e) return "";
  if (e.code === 1) return "위치 권한이 꺼져 있어요. 휴대폰 설정에서 이 앱의 위치 권한을 허용해 주세요.";
  if (e.code === 2) return "GPS 신호를 찾지 못했어요. 하늘이 트인 곳에서 휴대폰의 위치(GPS)가 켜져 있는지 확인해 주세요.";
  if (e.code === 3) return "위치를 찾는 데 시간이 걸리고 있어요. 하늘이 트인 곳으로 조금 옮겨 보세요.";
  return e.message || "위치를 알 수 없어요.";
}

export function dms(v, pos, neg) {
  const a = Math.abs(v);
  const d = Math.floor(a);
  const mf = (a - d) * 60;
  const m = Math.floor(mf);
  const s = ((mf - m) * 60).toFixed(1);
  return `${d}°${String(m).padStart(2, "0")}'${s.padStart(4, "0")}"${v >= 0 ? pos : neg}`;
}

export function distanceM(a, b) {
  const R = 6371000;
  const toR = (x) => (x * Math.PI) / 180;
  const dLat = toR(b.lat - a.lat);
  const dLon = toR(b.lon - a.lon);
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(toR(a.lat)) * Math.cos(toR(b.lat)) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}

export function bearingDeg(a, b) {
  const toR = (x) => (x * Math.PI) / 180;
  const y = Math.sin(toR(b.lon - a.lon)) * Math.cos(toR(b.lat));
  const x = Math.cos(toR(a.lat)) * Math.sin(toR(b.lat)) - Math.sin(toR(a.lat)) * Math.cos(toR(b.lat)) * Math.cos(toR(b.lon - a.lon));
  return ((Math.atan2(y, x) * 180) / Math.PI + 360) % 360;
}

const DIRS = ["북", "북동", "동", "남동", "남", "남서", "서", "북서"];
export function direction(deg) {
  return DIRS[Math.round(deg / 45) % 8];
}

export function fmtDistance(m) {
  return m < 1000 ? `${Math.round(m)}m` : `${(m / 1000).toFixed(m < 10000 ? 1 : 0)}km`;
}
