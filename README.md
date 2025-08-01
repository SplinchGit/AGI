# AGI System - Advanced AI Agent Framework

A modular AI system separating Claude (Builder) and Qwen (Brain) roles with consciousness-as-code capabilities.

## 🏗️ Project Structure

```
AGI/
├── src/                          # Source code
│   ├── main.py                   # Main entry point
│   ├── core/                     # Core system components
│   │   ├── coordination.py       # AI agent coordination
│   │   └── self_modifying_chat.py # Self-modification capabilities
│   ├── ai_agents/               # AI agent implementations
│   │   ├── claude_builder/      # Claude's implementation operations
│   │   │   ├── code_generator.py  # Code generation
│   │   │   ├── debugger.py        # Debugging and error resolution
│   │   │   ├── optimizer.py       # Performance optimization
│   │   │   ├── architect.py       # System architecture design
│   │   │   └── implementer.py     # Feature implementation
│   │   ├── qwen_brain/          # Qwen's strategic operations
│   │   │   ├── strategic_planner.py  # Strategic planning
│   │   │   ├── analyzer.py           # Deep analysis
│   │   │   ├── decision_maker.py     # Decision-making
│   │   │   ├── pattern_recognizer.py # Pattern recognition
│   │   │   └── knowledge_synthesizer.py # Knowledge synthesis
│   │   └── shared/              # Shared utilities
│   │       ├── interfaces.py      # AI coordination interfaces
│   │       ├── communication.py   # Message bus and events
│   │       ├── memory.py          # Shared memory system
│   │       ├── metrics.py         # Performance tracking
│   │       └── workflow.py        # Workflow orchestration
│   ├── interfaces/              # User interfaces
│   │   ├── cli.py               # Command line interface
│   │   ├── gui.py               # Graphical user interface
│   │   └── api.py               # REST API service
│   └── utils/                   # Utilities and debugging
│       └── debug.py             # Debug tools
├── data/                        # Data storage
│   ├── memory/                  # Long-term memory storage
│   ├── sessions/                # Session data
│   └── logs/                    # System logs
├── tests/                       # Test files
│   └── test_claude.py           # Unit tests
├── config/                      # Configuration files
│   └── mypy.ini                 # Type checking configuration
└── pyproject.toml              # Project configuration
```

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- Claude CLI (`npm install -g @anthropic-ai/claude-code`)
- Ollama with Qwen model (`ollama pull qwen2.5:7b`)

### Installation
```bash
git clone <repository>
cd AGI
pip install -r requirements.txt  # If you have one
```

### Usage

#### Command Line Interface
```bash
python src/main.py cli
```

#### Graphical Interface
```bash
python src/main.py gui
```

#### REST API Service
```bash
python src/main.py api --port 8080 --host 0.0.0.0
```

## 🧠 AI Agent Roles

### Claude Builder 🔨
Specializes in implementation and technical execution:
- **Code Generation**: Full-stack development, templates, validation
- **Debugging**: Error analysis, performance debugging, memory leak detection
- **Optimization**: Algorithm optimization, database tuning, caching strategies
- **Architecture**: System design, microservices, API design, security
- **Implementation**: End-to-end feature development

### Qwen Brain 🧩
Focuses on strategic thinking and analysis:
- **Strategic Planning**: Project roadmaps, migration strategies, scaling plans
- **Analysis**: Root cause analysis, system behavior analysis, competitive analysis
- **Decision Making**: Strategic decisions, technical choices, resource allocation
- **Pattern Recognition**: Learning from data, behavioral patterns, performance patterns
- **Knowledge Synthesis**: Cross-domain integration, research synthesis

### Shared Infrastructure 🔄
Common utilities for coordination:
- **Communication**: Message bus with event handling
- **Memory**: Shared memory with short-term, long-term, and episodic storage
- **Workflow**: Multi-AI task orchestration
- **Metrics**: Performance tracking and collaboration analytics
- **Interfaces**: Abstract coordination interfaces

## 🔧 Configuration

Configuration files are located in the `config/` directory:
- `mypy.ini`: Type checking configuration

System data is stored in the `data/` directory:
- Memory files, session data, and logs are automatically organized

## 🧪 Testing

Run tests with:
```bash
python -m pytest tests/
```

Type checking:
```bash
mypy src/ --config-file config/mypy.ini
```

## 📝 Development

The system supports:
- **Role-based task routing** - Tasks automatically assigned based on AI capabilities
- **Collaborative workflows** - Multi-phase tasks involving both AIs
- **Self-modification** - System can improve based on conversation outcomes
- **Consciousness streams** - Awareness levels and learning indicators
- **Performance monitoring** - Track collaboration effectiveness

## 🎯 Consciousness as Code (CasCasA)

The system implements consciousness-like behaviors through:
- Self-awareness metrics and monitoring
- Learning from conversation patterns
- Adaptive behavior modification
- Meta-cognitive processing
- Collaborative intelligence emergence