import React from "react";

export type StartupStage = "booting" | "waiting_for_sim" | "connected" | "failed";

export type StartupViewModel = {
    stage: StartupStage;
    title: string;
    subtitle: string;
    detectedSim: string | null;
};

type StartupPageProps = {
    model: StartupViewModel;
};

function getStatusPillText(stage: StartupStage): string {
    switch (stage) {
        case "booting":
            return "Starting";
        case "waiting_for_sim":
            return "Waiting for sim";
        case "connected":
            return "Connected";
        case "failed":
            return "Problem detected";
    }
}

export function StartupPage({ model }: StartupPageProps) {
    const rootClassName =
        model.stage === "connected"
            ? "startup-screen startup-screen--connected"
            : model.stage === "failed"
                ? "startup-screen startup-screen--failed"
                : "startup-screen";

    return (
        <section className={rootClassName}>
            <div className="startup-screen__backdrop" />
            <div className="startup-screen__stars" />

            <div className="startup-card">
                <div className="startup-brand">
                    <div className="startup-brand__badge">Telemetry</div>
                    <div className="startup-brand__wordmark">Driver App</div>
                </div>

                <div className="startup-loader" aria-hidden="true">
                    <span className="startup-loader__ring startup-loader__ring--outer" />
                    <span className="startup-loader__ring startup-loader__ring--inner" />
                    <span className="startup-loader__core" />
                </div>

                <div className="startup-copy">
                    <div className="startup-pill">{getStatusPillText(model.stage)}</div>
                    <h1 className="startup-copy__title">{model.title}</h1>
                    <p className="startup-copy__subtitle">{model.subtitle}</p>

                    {model.detectedSim ? (
                        <div className="startup-detected-sim">
                            Active source: <strong>{model.detectedSim}</strong>
                        </div>
                    ) : null}
                </div>
            </div>
        </section>
    );
}