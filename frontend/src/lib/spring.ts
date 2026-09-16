/**
 * A critically damped spring driven by requestAnimationFrame.
 *
 * Used instead of a CSS transition because a transition cannot be grabbed and
 * redirected mid-flight: it interpolates from a value captured when it started.
 * `SpringHandle.stop()` returns the live value and velocity, so a new gesture
 * can continue from exactly where the motion currently is.
 */
export interface SpringHandle {
  /** Cancels the animation and reports the value and velocity at this instant. */
  stop(): { value: number; velocity: number };
}

interface SpringOptions {
  from: number;
  to: number;
  /** Time to settle, in seconds. Apple's "response"; not a fixed duration. */
  response?: number;
  /** 1 = critically damped (no overshoot). Below 1 overshoots. */
  damping?: number;
  /** Initial velocity in units per second, handed over from a gesture. */
  velocity?: number;
  onFrame(value: number): void;
  onRest?(): void;
}

const EPSILON = 0.01;

export function spring({
  from,
  to,
  response = 0.35,
  damping = 1,
  velocity = 0,
  onFrame,
  onRest,
}: SpringOptions): SpringHandle {
  const omega = (2 * Math.PI) / response;
  let value = from;
  let speed = velocity;
  let previous = performance.now();
  let frame = 0;

  const tick = (now: number) => {
    // Clamp the step so a backgrounded tab cannot integrate a huge jump.
    const step = Math.min((now - previous) / 1000, 1 / 30);
    previous = now;

    const acceleration = -omega * omega * (value - to) - 2 * damping * omega * speed;
    speed += acceleration * step;
    value += speed * step;

    if (Math.abs(value - to) < EPSILON && Math.abs(speed) < EPSILON) {
      value = to;
      speed = 0;
      onFrame(value);
      onRest?.();
      return;
    }
    onFrame(value);
    frame = requestAnimationFrame(tick);
  };

  frame = requestAnimationFrame(tick);

  return {
    stop() {
      cancelAnimationFrame(frame);
      return { value, velocity: speed };
    },
  };
}
