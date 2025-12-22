import React, { useState } from 'react';

function Counter() {
  // 1. Define 'state'. count is the value, setCount is the function to change it.
  const [count, setCount] = useState(0);

  return (
    <div style={{ padding: '20px', textAlign: 'center' }}>
      <h1>You clicked {count} times</h1>
      
      {/* 2. Logic and UI are bundled together */}
      <button onClick={() => setCount(count + 1)}>
        Increase
      </button>
      
      <button onClick={() => setCount(count - 1)}>
        Decrease
      </button>
    </div>
  );
}

export default Counter;