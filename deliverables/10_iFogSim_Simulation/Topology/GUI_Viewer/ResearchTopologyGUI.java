package org.fog.gui.example;

import java.awt.BorderLayout;
import java.awt.Dimension;
import java.io.File;

import javax.swing.JFrame;
import javax.swing.JOptionPane;
import javax.swing.SwingUtilities;

import org.fog.gui.core.Bridge;
import org.fog.gui.core.Graph;
import org.fog.gui.core.GraphView;

/**
 * Displays the tested Local -> Edge -> Cloud topology using iFogSim's
 * existing GraphView GUI components.
 *
 * This is a visualization/import view. It does not launch the RL experiment.
 */
public class ResearchTopologyGUI extends JFrame {

    private static final long serialVersionUID = 1L;

    public ResearchTopologyGUI(String topologyPath) {
        super("Adaptive IoT Edge-Cloud - Research Topology");

        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setPreferredSize(new Dimension(1280, 800));
        setLayout(new BorderLayout());

        try {
            File jsonFile = new File(topologyPath).getAbsoluteFile();

            if (!jsonFile.isFile()) {
                throw new IllegalArgumentException(
                    "Cannot find topology JSON file:\n" + jsonFile
                );
            }

            Graph graph = Bridge.jsonToGraph(jsonFile.getAbsolutePath(), 0);
            GraphView canvas = new GraphView(graph);
            canvas.setPreferredSize(new Dimension(1200, 740));

            add(canvas, BorderLayout.CENTER);
            pack();
            setLocationRelativeTo(null);

        } catch (Exception ex) {
            JOptionPane.showMessageDialog(
                null,
                "Failed to load the iFogSim topology GUI.\n\n"
                    + ex.getClass().getSimpleName() + ": "
                    + ex.getMessage()
                    + "\n\nCheck that iFogSim GUI dependencies and resources "
                    + "are on the classpath.",
                "Topology GUI Error",
                JOptionPane.ERROR_MESSAGE
            );
            throw new RuntimeException("Could not open research topology", ex);
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            String jsonPath = args.length > 0
                ? args[0]
                : "research_topology.json";

            new ResearchTopologyGUI(jsonPath).setVisible(true);
        });
    }
}
