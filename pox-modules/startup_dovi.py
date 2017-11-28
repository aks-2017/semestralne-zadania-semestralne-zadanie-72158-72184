def launch ():
        from log.level import launch
        launch(DEBUG=True)

        from samples.pretty_log import launch
        launch()
        
        from openflow.discovery import launch
        launch()

        from topoDiscovery import launch
        launch()

        from latencyMonitor import launch
        launch()
