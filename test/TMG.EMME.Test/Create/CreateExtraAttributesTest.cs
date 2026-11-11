using System;
using System.Text.Json;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using TMG.Emme;
using TMG.Emme.Create;
using XTMF2;

namespace TMG.Emme.Test.Create;

[TestClass]
public class CreateExtraAttributesSerializationTest
{
    [TestMethod]
    [Timeout(30_000)]
    public void BuildParameters_SerializesScenarioAndAttributeDefinitions()
    {
        var action = new CreateExtraAttributes
        {
            ScenarioNumber = Helper.CreateParameter(42),
            Attributes = new[]
            {
                Helper.CreateParameter(new CreateExtraAttributes.AttributeDefinition
                {
                    Id = Helper.CreateParameter("@cost"),
                    Domain = Helper.CreateParameter(Domains.Link),
                    DefaultValue = Helper.CreateParameter(1.25f),
                    ResetToDefault = Helper.CreateParameter(false)
                }),
                Helper.CreateParameter(new CreateExtraAttributes.AttributeDefinition
                {
                    Id = Helper.CreateParameter("@boardings"),
                    Domain = Helper.CreateParameter(Domains.TransitSegment),
                    DefaultValue = Helper.CreateParameter(0.0f),
                    ResetToDefault = Helper.CreateParameter(true)
                })
            }
        };

        using var document = JsonDocument.Parse(action.BuildParameters());
        var root = document.RootElement;
        Assert.AreEqual(42, root.GetProperty("scenario_number").GetInt32());

        var attributes = root.GetProperty("attributes");
        Assert.AreEqual(2, attributes.GetArrayLength());
        Assert.AreEqual("@cost", attributes[0].GetProperty("id").GetString());
        Assert.AreEqual((int)Domains.Link, attributes[0].GetProperty("domain").GetInt32());
        Assert.AreEqual(1.25f, attributes[0].GetProperty("default_value").GetSingle());
        Assert.IsFalse(attributes[0].GetProperty("reset_to_default").GetBoolean());
        Assert.AreEqual("@boardings", attributes[1].GetProperty("id").GetString());
        Assert.AreEqual((int)Domains.TransitSegment, attributes[1].GetProperty("domain").GetInt32());
        Assert.IsTrue(attributes[1].GetProperty("reset_to_default").GetBoolean());
    }
}

[TestClass]
public class CreateExtraAttributesTest : TestBase
{
    [TestMethod]
    [Timeout(30_000)]
    public void Invoke_CreatesMultipleAttributesInScenario()
    {
        const int scenarioNumber = 1;
        Helper.ImportFrabitztownNetwork(scenarioNumber);

        var module = new CreateExtraAttributes
        {
            Name = nameof(CreateExtraAttributes),
            ScenarioNumber = Helper.CreateParameter(scenarioNumber),
            Attributes = new[]
            {
                Helper.CreateParameter(new CreateExtraAttributes.AttributeDefinition
                {
                    Id = Helper.CreateParameter("@tmgx"),
                    Domain = Helper.CreateParameter(Domains.Link),
                    DefaultValue = Helper.CreateParameter(0.0f),
                    ResetToDefault = Helper.CreateParameter(false)
                }),
                Helper.CreateParameter(new CreateExtraAttributes.AttributeDefinition
                {
                    Id = Helper.CreateParameter("@tmgy"),
                    Domain = Helper.CreateParameter(Domains.Node),
                    DefaultValue = Helper.CreateParameter(0.0f),
                    ResetToDefault = Helper.CreateParameter(false)
                })
            }
        };

        module.Invoke(Helper.Modeller);
    }
}

[TestClass]
public class CreateExtraAttributesEmptyInputTest
{
    [TestMethod]
    [Timeout(30_000)]
    public void Invoke_WithNullOrEmptyAttributes_DoesNotInvokeController()
    {
        var emptyModule = new CreateExtraAttributes
        {
            Attributes = Array.Empty<IFunction<CreateExtraAttributes.AttributeDefinition>>()
        };
        emptyModule.Invoke(null!);

        var nullModule = new CreateExtraAttributes
        {
            Attributes = null!
        };
        nullModule.Invoke(null!);
    }
}
