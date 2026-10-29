# Results release plan

How results go out without overloading the 2-core server. Students see their result on screen; the full result is the official tptv3-layout PDF, built before release.

## 1. The whole path

```mermaid
flowchart TD
    A[Testing Center Excel] --> B[Import scores<br/>match columns, check rows]
    B --> C[Admin approves<br/>scores saved, still hidden]
    C --> D[Queue builds PDFs<br/>1 at a time, quiet hours<br/>~1-1.5 h for 10,000]
    D --> E{All PDFs ready?}
    E -- not yet --> D
    E -- yes --> F[Release plan<br/>time, waves, PDF option]
    F --> G[Release at the set time]
    G --> H[Notices in waves<br/>~1,500 every 5 min]
    H --> I[Student opens result<br/>summary on screen, from cache]
    I --> J[Download full result PDF<br/>ready file, no building]
```

## 2. Why waves matter

```mermaid
xychart-beta
    title "Students arriving per minute after release (example, 9,088 students)"
    x-axis ["0", "5", "10", "15", "20", "25", "30", "35"]
    y-axis "Students per minute" 0 --> 3000
    bar [2800, 900, 400, 200, 100, 60, 40, 20]
    line [320, 320, 320, 320, 320, 320, 200, 80]
```

The bars are everyone told at once: a spike in the first minute. The line is the same students told in 6 waves: a steady, low stream the server handles easily.

## 3. What the server does at each moment

| Moment | Server work | Load |
|---|---|---|
| Import and check | Read one Excel file | Short |
| Build PDFs (night before) | 1 PDF at a time, pauses if the site is busy | Low, nobody online |
| Release | Send notices in waves (background) | Low |
| Student opens result | Send a small cached summary | Very low |
| Download PDF | Send a ready file | Very low |
| Score corrected later | Rebuild that one PDF | Tiny |

## 4. Admin controls

- **Publish → Release plan:** now or at a time; notify all at once or in waves (recommended); PDF ready before release (recommended), open after 1 hour, or off for now.
- **Checklist:** PDFs ready, scores approved, time set, server boost for results day (ask IT).
- **While it runs:** waves sent, students who opened their result, PDF downloads, server busy level; **Pause notifications** and **Pause PDF downloads**.
- **Hide results** any time.
