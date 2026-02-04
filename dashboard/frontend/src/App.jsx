import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import Experiments from './pages/Experiments'
import Architectures from './pages/Architectures'
import ExperimentDetail from './pages/ExperimentDetail'
import NotFound from './pages/NotFound'
import './styles/styles.css'

function App() {
    return (
        <Routes>
            <Route path="" element={<Layout />}>
                <Route index element={<Home />} />
                <Route path="experiments" element={<Experiments />} />
                <Route path="experiments/:id" element={<ExperimentDetail />} />
                <Route path="architectures" element={<Architectures />} />
                <Route path="*" element={<NotFound />} />
            </Route>
        </Routes>
    )
}

export default App
