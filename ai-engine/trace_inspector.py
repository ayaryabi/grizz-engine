#!/usr/bin/env python3
"""
Trace Inspector - Look up specific trace IDs from Agent SDK
"""
import sys
from agents import TracingProcessor, Trace, add_trace_processor
from typing import Optional, Dict, Any
import json

class TraceInspector(TracingProcessor):
    """Custom trace processor that can inspect specific traces"""
    
    def __init__(self):
        self.traces = {}  # Store traces by ID
        self.target_trace_id = None
        
    def set_target_trace(self, trace_id: str):
        """Set the trace ID we want to inspect"""
        self.target_trace_id = trace_id
        
    def process_trace(self, trace: Trace) -> None:
        """Process and store traces"""
        self.traces[trace.id] = trace
        
        # If this is our target trace, print detailed info
        if self.target_trace_id and trace.id == self.target_trace_id:
            self.print_trace_details(trace)
    
    # Required abstract methods
    def on_span_start(self, span):
        pass
    
    def on_span_end(self, span):
        pass
    
    def on_trace_start(self, trace):
        pass
    
    def on_trace_end(self, trace):
        pass
    
    def force_flush(self):
        pass
    
    def shutdown(self):
        pass
    
    def print_trace_details(self, trace: Trace):
        """Print detailed information about a trace"""
        print(f"\n🔍 TRACE ANALYSIS: {trace.id}")
        print("=" * 60)
        print(f"📊 Duration: {trace.duration}ms")
        print(f"🔧 Total Spans: {len(trace.spans)}")
        print()
        
        for i, span in enumerate(trace.spans, 1):
            print(f"📋 Span {i}: {span.name}")
            print(f"   ⏱️  Duration: {span.duration}ms")
            print(f"   🏷️  Type: {type(span.span_data).__name__}")
            
            # Show usage if available
            if hasattr(span.span_data, 'usage') and span.span_data.usage:
                usage = span.span_data.usage
                print(f"   🧮 Tokens: {usage}")
            
            # Show any metadata
            if hasattr(span.span_data, 'metadata') and span.span_data.metadata:
                print(f"   📝 Metadata: {span.span_data.metadata}")
            
            # Show input/output if available
            if hasattr(span.span_data, 'input'):
                input_preview = str(span.span_data.input)[:100] + "..." if len(str(span.span_data.input)) > 100 else str(span.span_data.input)
                print(f"   📥 Input: {input_preview}")
                
            if hasattr(span.span_data, 'output'):
                output_preview = str(span.span_data.output)[:100] + "..." if len(str(span.span_data.output)) > 100 else str(span.span_data.output)
                print(f"   📤 Output: {output_preview}")
            
            print()
        
        print("=" * 60)
    
    def lookup_trace(self, trace_id: str) -> Optional[Trace]:
        """Look up a stored trace by ID"""
        return self.traces.get(trace_id)
    
    def list_traces(self) -> Dict[str, Any]:
        """List all stored traces"""
        return {
            trace_id: {
                "duration": trace.duration,
                "spans": len(trace.spans),
                "span_names": [span.name for span in trace.spans]
            }
            for trace_id, trace in self.traces.items()
        }

# Global inspector instance
inspector = TraceInspector()
add_trace_processor(inspector)

def inspect_trace(trace_id: str):
    """Inspect a specific trace ID"""
    print(f"🔍 Looking for trace: {trace_id}")
    
    # Check if we already have it stored
    trace = inspector.lookup_trace(trace_id)
    if trace:
        print(f"✅ Found stored trace!")
        inspector.print_trace_details(trace)
    else:
        print(f"❌ Trace not found in current session.")
        print(f"💡 The trace might be from a previous session or still processing.")
        print(f"📋 Currently stored traces:")
        
        stored_traces = inspector.list_traces()
        if stored_traces:
            for tid, info in stored_traces.items():
                print(f"   • {tid}: {info['spans']} spans, {info['duration']}ms")
        else:
            print("   • No traces stored yet")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python trace_inspector.py <trace_id>")
        print("Example: python trace_inspector.py trace_38d15db304d0460fac9eaceb831c51ec")
        sys.exit(1)
    
    trace_id = sys.argv[1]
    inspect_trace(trace_id) 