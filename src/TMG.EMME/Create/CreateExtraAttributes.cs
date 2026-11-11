using XTMF2;
using TMG.Emme;

namespace TMG.Emme.Create;

[Module(Name = "Create Extra Attributes", Description = "Creates or initializes a set of extra attributes in an EMME scenario.",
    DocumentationLink = "http://tmg.utoronto.ca/doc/2.0")]
public sealed class CreateExtraAttributes : BaseAction<ModellerController>
{
    [Parameter(DefaultValue = "1", Index = 0, Name = "Scenario Number",
        Description = "The scenario in which to create the extra attributes.")]
    public IFunction<int> ScenarioNumber = null!;

    [SubModule(Name = "Extra Attributes", Description = "Extra attributes to create or initialize.", Index = 1)]
    public IFunction<AttributeDefinition>[] Attributes = null!;

    public override void Invoke(ModellerController context)
    {
        if (Attributes is null || Attributes.Length == 0)
        {
            return;
        }

        context.Run(this, "tmg2.Create.create_extra_attributes",
            BuildParameters(), LogbookLevel.Standard);
    }

    internal string BuildParameters()
    {
        return JSONParameterBuilder.BuildParameters(writer =>
        {
            writer.WriteNumber("scenario_number", ScenarioNumber.Invoke());
            writer.WriteStartArray("attributes");
            foreach (var attribute in Attributes)
            {
                attribute.Invoke().WriteParameters(writer);
            }
            writer.WriteEndArray();
        });
    }

    [Module(Name = "Extra Attribute", Description = "Defines an EMME extra attribute.",
        DocumentationLink = "http://tmg.utoronto.ca/doc/2.0")]
    public sealed class AttributeDefinition : IModule
    {
        [Parameter(DefaultValue = "@attribute", Index = 0, Name = "Attribute ID",
            Description = "The ID of the extra attribute.")]
        public IFunction<string> Id = null!;

        [Parameter(DefaultValue = "LINK", Index = 1, Name = "Domain",
            Description = "The EMME domain for the extra attribute.")]
        public IFunction<Domains> Domain = null!;

        [Parameter(DefaultValue = "0.0", Index = 2, Name = "Default Value",
            Description = "The initial or reset value for the extra attribute.")]
        public IFunction<float> DefaultValue = null!;

        [Parameter(DefaultValue = "false", Index = 3, Name = "Reset To Default",
            Description = "Initialize an existing attribute of the same domain to the default value.")]
        public IFunction<bool> ResetToDefault = null!;

        public string? Name { get; set; }

        public bool RuntimeValidation(ref string? error)
        {
            return true;
        }

        public void WriteParameters(System.Text.Json.Utf8JsonWriter writer)
        {
            writer.WriteStartObject();
            writer.WriteString("id", Id.Invoke());
            writer.WriteNumber("domain", (int)Domain.Invoke());
            writer.WriteNumber("default_value", DefaultValue.Invoke());
            writer.WriteBoolean("reset_to_default", ResetToDefault.Invoke());
            writer.WriteEndObject();
        }
    }
}
