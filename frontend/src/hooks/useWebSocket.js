import { useEffect, useRef } from 'react'
import useGameStore from '../store/useGameStore'

const useWebSocket = (url) => {
    const { setWinProbability, setGameTime, setConnectionStatus, updateLastTimestamp } = useGameStore()
    const ws = useRef(null)

    useEffect(() => {
        const connect = () => {
            ws.current = new WebSocket(url)

            ws.current.onopen = () => {
                console.log('WebSocket Connected')
                setConnectionStatus(true)
            }

            ws.current.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data)
                    if (data.type === 'update') {
                        setWinProbability(data.win_probability)
                        setGameTime(data.timestamp)
                        updateLastTimestamp()
                    }
                } catch (e) {
                    console.error('Error parsing WS message:', e)
                }
            }

            ws.current.onclose = () => {
                console.log('WebSocket Disconnected')
                setConnectionStatus(false)
                // Reconnect after 2 seconds
                setTimeout(connect, 2000)
            }

            ws.current.onerror = (error) => {
                console.error('WebSocket Error:', error)
                ws.current.close()
            }
        }

        connect()

        return () => {
            if (ws.current) {
                ws.current.close()
            }
        }
    }, [url, setWinProbability, setGameTime, setConnectionStatus, updateLastTimestamp])
}

export default useWebSocket
