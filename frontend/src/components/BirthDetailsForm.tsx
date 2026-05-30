import { useState } from "react";
import type { BirthDetails } from "../types";
import { Star, MapPin, Calendar, Clock, ChevronDown, ChevronUp } from "lucide-react";

interface Props {
  onSubmit: (details: BirthDetails) => void;
  initialValues?: BirthDetails;
  compact?: boolean;
}

function validate(v: Partial<BirthDetails>): string | null {
  if (!v.date) return "Birth date is required.";
  if (!/^\d{4}-\d{2}-\d{2}$/.test(v.date)) return "Date must be YYYY-MM-DD.";
  const d = new Date(v.date);
  if (isNaN(d.getTime()) || d > new Date()) return "Enter a valid past date.";
  if (!v.time) return "Birth time is required.";
  if (!/^\d{2}:\d{2}$/.test(v.time)) return "Time must be HH:MM (24-hour).";
  if (!v.place?.trim()) return "Birth place is required.";
  return null;
}

export default function BirthDetailsForm({ onSubmit, initialValues, compact }: Props) {
  const [open, setOpen] = useState(!compact);
  const [values, setValues] = useState<Partial<BirthDetails>>(initialValues ?? {});
  const [err, setErr] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(!!initialValues);

  const set = (key: keyof BirthDetails) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setValues((p) => ({ ...p, [key]: e.target.value }));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const validation = validate(values);
    if (validation) { setErr(validation); return; }
    setErr(null);
    setSubmitted(true);
    if (compact) setOpen(false);
    onSubmit(values as BirthDetails);
  };

  return (
    <div className="border border-gold-500/30 rounded-2xl bg-cosmos-800/60 backdrop-blur-sm overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-5 py-4 text-left"
      >
        <div className="flex items-center gap-2">
          <Star className="w-4 h-4 text-gold-400" />
          <span className="font-serif text-gold-300 text-sm tracking-wide">
            {submitted ? "Your Birth Details" : "Share Your Birth Details"}
          </span>
          {submitted && (
            <span className="text-xs text-cream-dim ml-1">
              · {values.date} · {values.time} · {values.place}
            </span>
          )}
        </div>
        {compact && (open ? <ChevronUp className="w-4 h-4 text-cream-dim" /> : <ChevronDown className="w-4 h-4 text-cream-dim" />)}
      </button>

      {open && (
        <form onSubmit={handleSubmit} className="px-5 pb-5 space-y-4 animate-fade-in">
          <p className="text-cream-dim text-xs leading-relaxed">
            Accurate chart readings require your birth date, time, and city. Time of birth affects your
            Ascendant and house placements significantly.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <label className="space-y-1">
              <span className="flex items-center gap-1.5 text-xs text-cream-dim">
                <Calendar className="w-3 h-3" /> Date of Birth
              </span>
              <input
                type="date"
                value={values.date ?? ""}
                onChange={set("date")}
                max={new Date().toISOString().split("T")[0]}
                className="w-full bg-cosmos-900 border border-cosmos-700 rounded-xl px-3 py-2 text-cream text-sm focus:outline-none focus:border-gold-500/60 focus:ring-1 focus:ring-gold-500/20 transition"
                placeholder="YYYY-MM-DD"
              />
            </label>

            <label className="space-y-1">
              <span className="flex items-center gap-1.5 text-xs text-cream-dim">
                <Clock className="w-3 h-3" /> Time of Birth
              </span>
              <input
                type="time"
                value={values.time ?? ""}
                onChange={set("time")}
                className="w-full bg-cosmos-900 border border-cosmos-700 rounded-xl px-3 py-2 text-cream text-sm focus:outline-none focus:border-gold-500/60 focus:ring-1 focus:ring-gold-500/20 transition"
              />
            </label>
          </div>

          <label className="block space-y-1">
            <span className="flex items-center gap-1.5 text-xs text-cream-dim">
              <MapPin className="w-3 h-3" /> City of Birth
            </span>
            <input
              type="text"
              value={values.place ?? ""}
              onChange={set("place")}
              placeholder="e.g. Mumbai, India"
              className="w-full bg-cosmos-900 border border-cosmos-700 rounded-xl px-3 py-2 text-cream text-sm focus:outline-none focus:border-gold-500/60 focus:ring-1 focus:ring-gold-500/20 transition"
            />
          </label>

          {err && (
            <p className="text-red-400 text-xs">{err}</p>
          )}

          <button
            type="submit"
            className="w-full py-2.5 rounded-xl bg-gradient-to-r from-gold-500 to-gold-400 text-cosmos-900 font-medium text-sm tracking-wide hover:from-gold-400 hover:to-gold-300 transition-all duration-200"
          >
            {submitted ? "Update Details" : "Begin My Reading"}
          </button>
        </form>
      )}
    </div>
  );
}
