// The one focus element every panel and view follows, with a history for back.

export function createFocus() {
  let current = null;
  const subscribers = new Set();
  const history = [];
  const notify = () => subscribers.forEach((fn) => fn(current));
  return {
    history,
    get: () => current,
    setFocus(key) {
      if (!key || key === current) return;
      if (current) history.push(current);
      current = key;
      notify();
    },
    back() {
      if (!history.length) return;
      current = history.pop();
      notify();
    },
    subscribe(fn) {
      subscribers.add(fn);
      return () => subscribers.delete(fn);
    },
  };
}

export const focus = createFocus();
export const { setFocus, subscribe, back, history } = focus;

/** Keys from the root owner down to `key`, following a child -> owner map. */
export function breadcrumb(key, parents) {
  const path = [];
  for (let k = key; k && !path.includes(k); k = parents.get(k)) path.unshift(k);
  return path;
}
